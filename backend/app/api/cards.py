"""Cards API endpoints."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.card import CardConfig, UserBenefitSettings, UserCard
from app.models.user import User
from app.schemas.card import (
    BenefitSettingResponse,
    BenefitSettingUpdate,
    CardConfigResponse,
    UserCardCreate,
    UserCardResponse,
    UserCardUpdate,
)

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/available", response_model=list[CardConfigResponse])
def get_available_cards(db: Session = Depends(get_db)):
    """Get all available card configurations (no auth required)."""
    configs = db.query(CardConfig).all()
    return configs


@router.get("/my", response_model=list[UserCardResponse])
def get_my_cards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's card portfolio."""
    user_cards = db.query(UserCard).filter(UserCard.user_id == current_user.id).all()
    
    # Build response with card details
    result = []
    for uc in user_cards:
        result.append(UserCardResponse(
            id=uc.id,
            card_config_id=uc.card_config_id,
            card_slug=uc.card_config.slug,
            card_name=uc.card_config.name,
            card_issuer=uc.card_config.issuer,
            nickname=uc.nickname,
            card_anniversary=uc.card_anniversary,
            active=bool(uc.active),
            added_at=uc.added_at,
        ))
    
    return result


@router.post("/my", response_model=UserCardResponse, status_code=status.HTTP_201_CREATED)
def add_card_to_portfolio(
    card_data: UserCardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a card to user's portfolio."""
    # Verify card config exists
    card_config = db.query(CardConfig).filter(CardConfig.id == card_data.card_config_id).first()
    if not card_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card configuration not found",
        )
    
    # Check if user already has this card
    existing = db.query(UserCard).filter(
        UserCard.user_id == current_user.id,
        UserCard.card_config_id == card_data.card_config_id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Card already in portfolio",
        )
    
    # Create user card
    user_card = UserCard(
        user_id=current_user.id,
        card_config_id=card_data.card_config_id,
        nickname=card_data.nickname,
        card_anniversary=card_data.card_anniversary,
    )
    db.add(user_card)
    db.commit()
    db.refresh(user_card)
    
    return UserCardResponse(
        id=user_card.id,
        card_config_id=user_card.card_config_id,
        card_slug=card_config.slug,
        card_name=card_config.name,
        card_issuer=card_config.issuer,
        nickname=user_card.nickname,
        card_anniversary=user_card.card_anniversary,
        active=bool(user_card.active),
        added_at=user_card.added_at,
    )


@router.patch("/my/{user_card_id}", response_model=UserCardResponse)
def update_user_card(
    user_card_id: str,
    card_data: UserCardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a card in user's portfolio."""
    user_card = db.query(UserCard).filter(
        UserCard.id == user_card_id,
        UserCard.user_id == current_user.id,
    ).first()
    
    if not user_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found in your portfolio",
        )
    
    # Update fields
    if card_data.nickname is not None:
        user_card.nickname = card_data.nickname
    if card_data.card_anniversary is not None:
        user_card.card_anniversary = card_data.card_anniversary
    if card_data.active is not None:
        user_card.active = 1 if card_data.active else 0
    
    db.commit()
    db.refresh(user_card)
    
    return UserCardResponse(
        id=user_card.id,
        card_config_id=user_card.card_config_id,
        card_slug=user_card.card_config.slug,
        card_name=user_card.card_config.name,
        card_issuer=user_card.card_config.issuer,
        nickname=user_card.nickname,
        card_anniversary=user_card.card_anniversary,
        active=bool(user_card.active),
        added_at=user_card.added_at,
    )


@router.delete("/my/{user_card_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_card_from_portfolio(
    user_card_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a card from user's portfolio."""
    user_card = db.query(UserCard).filter(
        UserCard.id == user_card_id,
        UserCard.user_id == current_user.id,
    ).first()
    
    if not user_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found in your portfolio",
        )
    
    db.delete(user_card)
    db.commit()


# Benefit settings endpoints

@router.get("/my/{user_card_id}/benefits/settings", response_model=list[BenefitSettingResponse])
def get_benefit_settings(
    user_card_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get benefit settings (muting) for a user's card."""
    user_card = db.query(UserCard).filter(
        UserCard.id == user_card_id,
        UserCard.user_id == current_user.id,
    ).first()
    
    if not user_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found in your portfolio",
        )
    
    settings = db.query(UserBenefitSettings).filter(
        UserBenefitSettings.user_card_id == user_card_id,
    ).all()
    
    return settings


@router.put("/my/{user_card_id}/benefits/settings", response_model=BenefitSettingResponse)
def update_benefit_setting(
    user_card_id: str,
    setting_data: BenefitSettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a benefit setting (mute/unmute, add notes)."""
    user_card = db.query(UserCard).filter(
        UserCard.id == user_card_id,
        UserCard.user_id == current_user.id,
    ).first()
    
    if not user_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found in your portfolio",
        )
    
    # Find or create setting
    setting = db.query(UserBenefitSettings).filter(
        UserBenefitSettings.user_card_id == user_card_id,
        UserBenefitSettings.benefit_slug == setting_data.benefit_slug,
    ).first()
    
    if not setting:
        setting = UserBenefitSettings(
            user_id=current_user.id,
            user_card_id=user_card_id,
            benefit_slug=setting_data.benefit_slug,
        )
        db.add(setting)
    
    # Update fields
    if setting_data.muted is not None:
        setting.muted = 1 if setting_data.muted else 0
        setting.muted_at = datetime.utcnow().isoformat() if setting_data.muted else None
    if setting_data.notes is not None:
        setting.notes = setting_data.notes
    
    db.commit()
    db.refresh(setting)
    
    return setting
