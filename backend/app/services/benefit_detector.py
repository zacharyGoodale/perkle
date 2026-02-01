"""Benefit detection service for auto-detecting used benefits from transactions."""
import json
import re
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.benefit import BenefitPeriod
from app.models.card import CardConfig, UserCard, UserBenefitSettings
from app.models.transaction import Transaction
from app.services.benefit_periods import get_period_boundaries


def parse_anniversary_to_date(anniversary_str: str, reference_date: date) -> date:
    """Convert MM-DD or YYYY-MM-DD anniversary string to a date object.
    
    For MM-DD format, uses the reference year to construct a full date.
    """
    if not anniversary_str:
        return None
    
    # Handle both old YYYY-MM-DD and new MM-DD formats
    if len(anniversary_str) == 10:  # YYYY-MM-DD
        return datetime.strptime(anniversary_str, "%Y-%m-%d").date()
    elif len(anniversary_str) == 5:  # MM-DD
        month, day = int(anniversary_str[:2]), int(anniversary_str[3:])
        return date(reference_date.year, month, day)
    else:
        return None


def detect_benefits_for_user(
    db: Session,
    user_id: str,
) -> dict:
    """Scan all credit transactions and detect benefit usage.
    
    Returns dict with detected benefits and any new BenefitPeriod records created.
    """
    # Get user's cards
    user_cards = db.query(UserCard).filter(
        UserCard.user_id == user_id,
        UserCard.active == 1,
    ).all()
    
    if not user_cards:
        return {"detected": 0, "cards_checked": 0}
    
    detected_count = 0
    cards_checked = len(user_cards)
    detected_benefits = []
    
    # Track periods created in this run to avoid duplicates
    created_periods: set[tuple] = set()  # (user_card_id, benefit_slug, period_start)
    
    today = date.today()

    for user_card in user_cards:
        card_config = user_card.card_config
        benefits = json.loads(card_config.benefits)
        
        # Get card anniversary for cardmember_year benefits
        card_anniversary = None
        if user_card.card_anniversary:
            try:
                card_anniversary = parse_anniversary_to_date(user_card.card_anniversary, date.today())
            except ValueError:
                pass
        
        # Get all credit transactions for this card
        credits = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.card_config_id == card_config.id,
            Transaction.amount < 0,  # Credits are negative
        ).all()
        
        for benefit in benefits:
            if benefit.get("tracking_mode") != "auto":
                continue
                
            detection_rules = benefit.get("detection_rules", {})
            credit_patterns = detection_rules.get("credit_patterns", [])
            
            if not credit_patterns:
                continue

            cadence = benefit.get("cadence", "monthly")
            reset_type = benefit.get("reset_type")
            effective_anniversary = card_anniversary if reset_type == "cardmember_year" else None
            period_start, period_end = get_period_boundaries(
                cadence=cadence,
                reference_date=today,
                card_anniversary=effective_anniversary,
                reset_type=reset_type,
            )

            # Find matching credit transactions
            for txn in credits:
                txn_date = _parse_transaction_date(txn.date)
                if not txn_date:
                    continue
                if txn_date < period_start or txn_date > period_end:
                    continue
                if _matches_patterns(txn.name, credit_patterns):
                    # Found a matching credit - create/update benefit period
                    result = _record_benefit_usage(
                        db=db,
                        user_card=user_card,
                        benefit=benefit,
                        transaction=txn,
                        card_anniversary=card_anniversary,
                        reset_type=reset_type,
                        txn_date=txn_date,
                        period_start=period_start,
                        period_end=period_end,
                        created_periods=created_periods,
                    )
                    if result:
                        detected_count += 1
                        detected_benefits.append({
                            "card": card_config.name,
                            "benefit": benefit["name"],
                            "amount": abs(txn.amount),
                            "date": txn.date,
                            "transaction": txn.name,
                        })
                        
                        # Update transaction with benefit slug
                        txn.benefit_slug = benefit["slug"]
    
    db.commit()
    
    return {
        "detected": detected_count,
        "cards_checked": cards_checked,
        "benefits": detected_benefits,
    }


def _matches_patterns(text: str, patterns: list[str]) -> bool:
    """Check if text matches any of the patterns (case-insensitive)."""
    text_lower = text.lower()
    for pattern in patterns:
        # Simple substring match (case-insensitive)
        if pattern.lower() in text_lower:
            return True
    return False


def _parse_transaction_date(date_str: str) -> date | None:
    """Parse a transaction date string into a date object."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def _record_benefit_usage(
    db: Session,
    user_card: UserCard,
    benefit: dict,
    transaction: Transaction,
    card_anniversary: date | None,
    reset_type: str | None,
    txn_date: date,
    period_start: date,
    period_end: date,
    created_periods: set[tuple],
) -> BenefitPeriod | None:
    """Record benefit usage, creating or updating a BenefitPeriod.
    
    Returns the BenefitPeriod if newly recorded, None if already exists.
    """
    # Ensure period boundaries align with current benefit cadence.
    if not period_start or not period_end:
        cadence = benefit.get("cadence", "monthly")
        effective_anniversary = card_anniversary if reset_type == "cardmember_year" else None
        period_start, period_end = get_period_boundaries(
            cadence=cadence,
            reference_date=txn_date,
            card_anniversary=effective_anniversary,
            reset_type=reset_type,
        )

    # Create period key for tracking
    period_key = (user_card.id, benefit["slug"], period_start.isoformat())
    txn_amount = abs(transaction.amount)
    benefit_value = benefit.get("value", 0)
    
    # Check if we already have this benefit period recorded in DB
    existing = db.query(BenefitPeriod).filter(
        BenefitPeriod.user_card_id == user_card.id,
        BenefitPeriod.benefit_slug == benefit["slug"],
        BenefitPeriod.period_start == period_start.isoformat(),
    ).first()
    
    if existing:
        # Already recorded - ACCUMULATE the amount (benefits like travel credit add up)
        existing.amount_used = existing.amount_used + txn_amount
        existing.usage_count = (existing.usage_count or 0) + 1
        # Check if now complete
        if existing.amount_used >= benefit_value and not existing.completed:
            existing.completed = 1
            existing.completed_at = datetime.utcnow().isoformat()
        return None  # Not a new detection, just an update
    
    # Check if we already created this period in this run (not yet in DB)
    if period_key in created_periods:
        # Find the pending object and update it
        # Since it's not committed yet, we need to find it in the session
        for obj in db.new:
            if (isinstance(obj, BenefitPeriod) and 
                obj.user_card_id == user_card.id and
                obj.benefit_slug == benefit["slug"] and
                obj.period_start == period_start.isoformat()):
                obj.amount_used = obj.amount_used + txn_amount
                obj.usage_count = (obj.usage_count or 0) + 1
                if obj.amount_used >= benefit_value and not obj.completed:
                    obj.completed = 1
                    obj.completed_at = datetime.utcnow().isoformat()
                return None
        return None
    
    # Mark this period as being created
    created_periods.add(period_key)
    
    # Create new benefit period record
    benefit_period = BenefitPeriod(
        user_card_id=user_card.id,
        benefit_slug=benefit["slug"],
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat(),
        amount_limit=benefit_value,
        amount_used=txn_amount,
        usage_count=1,
        completed=1 if txn_amount >= benefit_value else 0,
        completed_at=datetime.utcnow().isoformat() if txn_amount >= benefit_value else None,
    )
    db.add(benefit_period)
    
    return benefit_period


def get_benefit_status_for_user(
    db: Session,
    user_id: str,
    include_hidden: bool = False,
) -> list[dict]:
    """Get current benefit status for all user's cards.
    
    Returns list of benefit statuses with period info.
    """
    user_cards = db.query(UserCard).filter(
        UserCard.user_id == user_id,
        UserCard.active == 1,
    ).all()
    
    today = date.today()
    result = []
    
    # Get all hidden settings for this user
    hidden_settings = db.query(UserBenefitSettings).filter(
        UserBenefitSettings.user_id == user_id,
        UserBenefitSettings.muted == 1,
    ).all()
    hidden_map = {(s.user_card_id, s.benefit_slug): True for s in hidden_settings}
    
    for user_card in user_cards:
        card_config = user_card.card_config
        benefits = json.loads(card_config.benefits)
        
        # Get card anniversary
        card_anniversary = None
        if user_card.card_anniversary:
            try:
                card_anniversary = parse_anniversary_to_date(user_card.card_anniversary, date.today())
            except ValueError:
                pass
        
        # Calculate days until renewal (next anniversary date)
        days_until_renewal = None
        next_renewal_date = None
        if card_anniversary:
            next_anniversary = date(today.year, card_anniversary.month, card_anniversary.day)
            if next_anniversary <= today:
                next_anniversary = date(today.year + 1, card_anniversary.month, card_anniversary.day)
            days_until_renewal = (next_anniversary - today).days
            next_renewal_date = next_anniversary.isoformat()
        
        card_status = {
            "user_card_id": user_card.id,
            "card_name": card_config.name,
            "card_slug": card_config.slug,
            "card_anniversary": user_card.card_anniversary,
            "next_renewal_date": next_renewal_date,
            "annual_fee": card_config.annual_fee,
            "benefits_url": card_config.benefits_url,
            "days_until_renewal": days_until_renewal,
            "benefits": [],
        }
        
        for benefit in benefits:
            # Check if hidden
            is_hidden = (user_card.id, benefit["slug"]) in hidden_map
            if is_hidden and not include_hidden:
                continue
            
            tracking_mode = benefit.get("tracking_mode", "manual")
            cadence = benefit.get("cadence", "monthly")
            reset_type = benefit.get("reset_type")
            effective_anniversary = card_anniversary if reset_type == "cardmember_year" else None
            
            # Get current period
            period_start, period_end = get_period_boundaries(
                cadence=cadence,
                reference_date=today,
                card_anniversary=effective_anniversary,
                reset_type=reset_type,
            )
            
            # Check if there's a recorded usage for this period
            period_record = db.query(BenefitPeriod).filter(
                BenefitPeriod.user_card_id == user_card.id,
                BenefitPeriod.benefit_slug == benefit["slug"],
                BenefitPeriod.period_start == period_start.isoformat(),
            ).first()
            
            days_left = (period_end - today).days
            
            # Determine status
            # Info-only benefits (like anniversary bonus) are always "info"
            if tracking_mode == "info":
                status = "info"
            elif period_record and period_record.completed:
                status = "used"
            elif period_record and period_record.amount_used > 0:
                status = "partial"
            elif days_left <= 0:
                status = "expired"
            elif days_left <= 7:
                status = "expiring"
            else:
                status = "available"
            
            card_status["benefits"].append({
                "slug": benefit["slug"],
                "name": benefit["name"],
                "value": benefit.get("value", 0),
                "cadence": cadence,
                "tracking_mode": tracking_mode,
                "reset_type": reset_type,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "days_remaining": max(0, days_left),
                "status": status,
                "amount_used": period_record.amount_used if period_record else 0,
                "amount_limit": benefit.get("value", 0),
                "notes": benefit.get("notes"),
                "hidden": is_hidden,
            })
        
        result.append(card_status)
    
    return result
