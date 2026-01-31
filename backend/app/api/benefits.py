"""Benefits API endpoints."""
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.benefit import BenefitPeriod
from app.models.card import UserCard
from app.models.user import User
from app.schemas.benefit import (
    BenefitPeriodResponse,
    BenefitStatusResponse,
    CardBenefitStatus,
    DetectionResponse,
    ManualBenefitMarkRequest,
)
from app.services.benefit_detector import (
    detect_benefits_for_user,
    get_benefit_status_for_user,
)
from app.services.benefit_periods import get_period_boundaries

router = APIRouter(prefix="/benefits", tags=["benefits"])


@router.get("/status", response_model=BenefitStatusResponse)
def get_benefit_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current benefit status for all user's cards (dashboard view)."""
    cards_status = get_benefit_status_for_user(db, current_user.id)
    
    # Calculate summary stats
    total_available = 0
    total_used = 0
    expiring_count = 0
    
    for card in cards_status:
        for benefit in card["benefits"]:
            if benefit["status"] == "used":
                total_used += benefit["amount_used"]
            elif benefit["status"] in ("available", "expiring"):
                total_available += benefit["amount_limit"]
            if benefit["status"] == "expiring":
                expiring_count += 1
    
    return BenefitStatusResponse(
        cards=[CardBenefitStatus(**c) for c in cards_status],
        summary={
            "total_available_value": total_available,
            "total_used_value": total_used,
            "expiring_soon_count": expiring_count,
            "cards_count": len(cards_status),
        },
    )


@router.post("/detect", response_model=DetectionResponse)
def detect_benefits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run benefit detection on all user's transactions."""
    result = detect_benefits_for_user(db, current_user.id)
    return DetectionResponse(**result)


@router.post("/mark-used", response_model=BenefitPeriodResponse)
def mark_benefit_used(
    request: ManualBenefitMarkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually mark a benefit as used (for manual tracking mode)."""
    # Verify user owns this card
    user_card = db.query(UserCard).filter(
        UserCard.id == request.user_card_id,
        UserCard.user_id == current_user.id,
    ).first()
    
    if not user_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found in your portfolio",
        )
    
    # Get benefit config to determine cadence
    import json
    benefits = json.loads(user_card.card_config.benefits)
    benefit_config = next(
        (b for b in benefits if b["slug"] == request.benefit_slug),
        None,
    )
    
    if not benefit_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benefit not found for this card",
        )
    
    # Calculate current period
    cadence = benefit_config.get("cadence", "monthly")
    reset_type = benefit_config.get("reset_type")
    
    card_anniversary = None
    if user_card.card_anniversary and reset_type == "cardmember_year":
        card_anniversary = datetime.strptime(user_card.card_anniversary, "%Y-%m-%d").date()
    
    period_start, period_end = get_period_boundaries(
        cadence=cadence,
        reference_date=date.today(),
        card_anniversary=card_anniversary,
    )
    
    # Check if period already exists
    existing = db.query(BenefitPeriod).filter(
        BenefitPeriod.user_card_id == request.user_card_id,
        BenefitPeriod.benefit_slug == request.benefit_slug,
        BenefitPeriod.period_start == period_start.isoformat(),
    ).first()
    
    benefit_limit = benefit_config.get("value", 0)
    
    # Validate amount if provided
    if request.amount is not None:
        if request.amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be greater than zero",
            )
    
    if existing:
        # Calculate new total
        amount_to_add = request.amount if request.amount is not None else (benefit_limit - existing.amount_used)
        new_total = existing.amount_used + amount_to_add
        
        # Validate doesn't exceed limit
        if new_total > benefit_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Amount would exceed benefit limit (${benefit_limit}). Current: ${existing.amount_used:.2f}, Adding: ${amount_to_add:.2f}",
            )
        
        # Update existing period - ACCUMULATE the amount
        existing.manual_checked = 1
        existing.amount_used = new_total
        existing.usage_count = (existing.usage_count or 0) + 1
        
        # Mark completed if we've hit the limit
        if new_total >= benefit_limit:
            existing.completed = 1
            existing.completed_at = datetime.utcnow().isoformat()
        
        if request.notes:
            existing.manual_notes = request.notes
        db.commit()
        db.refresh(existing)
        return BenefitPeriodResponse(
            id=existing.id,
            benefit_slug=existing.benefit_slug,
            period_start=existing.period_start,
            period_end=existing.period_end,
            amount_limit=existing.amount_limit,
            amount_used=existing.amount_used,
            completed=bool(existing.completed),
            manual_checked=bool(existing.manual_checked),
            manual_notes=existing.manual_notes,
        )
    
    # Create new period
    amount = request.amount if request.amount is not None else benefit_limit
    
    # Validate doesn't exceed limit for new period
    if amount > benefit_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Amount (${amount:.2f}) exceeds benefit limit (${benefit_limit})",
        )
    
    benefit_period = BenefitPeriod(
        user_card_id=request.user_card_id,
        benefit_slug=request.benefit_slug,
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat(),
        amount_limit=benefit_limit,
        amount_used=amount,
        usage_count=1,
        completed=1 if amount >= benefit_limit else 0,
        completed_at=datetime.utcnow().isoformat() if amount >= benefit_limit else None,
        manual_checked=1,
        manual_amount=amount,
        manual_notes=request.notes,
    )
    db.add(benefit_period)
    db.commit()
    db.refresh(benefit_period)
    
    return BenefitPeriodResponse(
        id=benefit_period.id,
        benefit_slug=benefit_period.benefit_slug,
        period_start=benefit_period.period_start,
        period_end=benefit_period.period_end,
        amount_limit=benefit_period.amount_limit,
        amount_used=benefit_period.amount_used,
        completed=bool(benefit_period.completed),
        manual_checked=bool(benefit_period.manual_checked),
        manual_notes=benefit_period.manual_notes,
    )


@router.get("/history/{user_card_id}/{benefit_slug}", response_model=list[BenefitPeriodResponse])
def get_benefit_history(
    user_card_id: str,
    benefit_slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get history of a benefit's usage across periods."""
    # Verify user owns this card
    user_card = db.query(UserCard).filter(
        UserCard.id == user_card_id,
        UserCard.user_id == current_user.id,
    ).first()
    
    if not user_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found in your portfolio",
        )
    
    periods = db.query(BenefitPeriod).filter(
        BenefitPeriod.user_card_id == user_card_id,
        BenefitPeriod.benefit_slug == benefit_slug,
    ).order_by(BenefitPeriod.period_start.desc()).all()
    
    return [
        BenefitPeriodResponse(
            id=p.id,
            benefit_slug=p.benefit_slug,
            period_start=p.period_start,
            period_end=p.period_end,
            amount_limit=p.amount_limit,
            amount_used=p.amount_used,
            completed=bool(p.completed),
            manual_checked=bool(p.manual_checked),
            manual_notes=p.manual_notes,
        )
        for p in periods
    ]
