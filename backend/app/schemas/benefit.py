"""Benefit schemas."""
from pydantic import BaseModel


class BenefitStatusItem(BaseModel):
    """Status of a single benefit in current period."""
    
    slug: str
    name: str
    value: float
    cadence: str
    tracking_mode: str  # auto, manual, info
    reset_type: str | None = None  # calendar_year, cardmember_year, rolling_years
    period_start: str
    period_end: str
    days_remaining: int
    status: str  # used, partial, expired, expiring, available, info
    amount_used: float
    amount_limit: float
    notes: str | None
    muted: bool = False


class CardBenefitStatus(BaseModel):
    """All benefit statuses for a card."""
    
    user_card_id: str
    card_name: str
    card_slug: str
    card_anniversary: str | None = None
    annual_fee: int = 0
    days_until_renewal: int | None = None  # Days until next annual fee
    benefits: list[BenefitStatusItem]


class BenefitStatusResponse(BaseModel):
    """Response with all cards' benefit statuses."""
    
    cards: list[CardBenefitStatus]
    summary: dict  # Quick stats


class ManualBenefitMarkRequest(BaseModel):
    """Request to manually mark a benefit as used."""
    
    user_card_id: str
    benefit_slug: str
    amount: float | None = None
    notes: str | None = None


class BenefitPeriodResponse(BaseModel):
    """Benefit period record."""
    
    id: str
    benefit_slug: str
    period_start: str
    period_end: str
    amount_limit: float
    amount_used: float
    completed: bool
    manual_checked: bool
    manual_notes: str | None
    
    class Config:
        from_attributes = True


class DetectionResponse(BaseModel):
    """Response from running benefit detection."""
    
    detected: int
    cards_checked: int
    benefits: list[dict]
