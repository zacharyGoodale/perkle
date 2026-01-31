"""Card schemas."""
import json
from typing import Any

from pydantic import BaseModel, Field, field_validator


class BenefitConfig(BaseModel):
    """Benefit configuration from YAML."""
    
    slug: str
    name: str
    value: float
    cadence: str  # monthly, quarterly, semi-annual, annual, one-time, per-booking
    tracking_mode: str  # auto, manual
    notes: str | None = None
    reset_type: str | None = None  # cardmember_year for anniversary-based
    reset_years: int | None = None  # for one-time benefits
    detection_rules: dict | None = None


class CardConfigResponse(BaseModel):
    """Card configuration response (available cards)."""
    
    id: str
    slug: str
    name: str
    issuer: str
    annual_fee: int
    benefits_url: str | None = None
    benefits: list[BenefitConfig]
    
    @field_validator("benefits", mode="before")
    @classmethod
    def parse_benefits(cls, v: Any) -> list[dict]:
        if isinstance(v, str):
            return json.loads(v)
        return v
    
    class Config:
        from_attributes = True


class UserCardCreate(BaseModel):
    """Request to add a card to user's portfolio."""
    
    card_config_id: str
    nickname: str | None = None
    card_anniversary: str | None = Field(
        None,
        description="Card anniversary date (MM-DD) for cardmember_year benefits"
    )


class UserCardUpdate(BaseModel):
    """Request to update a user's card."""
    
    nickname: str | None = None
    card_anniversary: str | None = None
    active: bool | None = None


class UserCardResponse(BaseModel):
    """User's card in their portfolio."""
    
    id: str
    card_config_id: str
    card_slug: str
    card_name: str
    card_issuer: str
    nickname: str | None
    card_anniversary: str | None
    active: bool
    added_at: str
    
    class Config:
        from_attributes = True


class BenefitSettingUpdate(BaseModel):
    """Update hidden/notes for a benefit."""
    
    benefit_slug: str
    hidden: bool | None = None
    notes: str | None = None


class BenefitSettingResponse(BaseModel):
    """User's settings for a benefit."""
    
    id: str
    user_card_id: str
    benefit_slug: str
    hidden: bool = Field(validation_alias="muted")
    notes: str | None
    
    @field_validator("hidden", mode="before")
    @classmethod
    def int_to_bool(cls, v: Any) -> bool:
        if isinstance(v, int):
            return bool(v)
        return v
    
    class Config:
        from_attributes = True
        populate_by_name = True
