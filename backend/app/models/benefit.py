"""Benefit tracking models."""
import uuid
from datetime import datetime

from sqlalchemy import Column, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class BenefitPeriod(Base):
    """Tracks benefit usage within a period (monthly, annual, one-time, etc.)."""
    
    __tablename__ = "benefit_periods"
    __table_args__ = (
        UniqueConstraint("user_card_id", "benefit_slug", "period_start", name="uq_benefit_period"),
        Index("ix_benefit_periods_active", "user_card_id", "period_end"),
    )
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_card_id = Column(String(36), ForeignKey("user_cards.id", ondelete="CASCADE"), nullable=False)
    benefit_slug = Column(String(50), nullable=False)
    
    # Period boundaries
    period_start = Column(String(10), nullable=False)  # YYYY-MM-DD
    period_end = Column(String(10), nullable=False)  # YYYY-MM-DD
    
    # Usage tracking
    amount_limit = Column(Float, nullable=False)  # Total available in period
    amount_used = Column(Float, default=0.0)  # Amount used so far
    usage_count = Column(Integer, default=0)  # Number of uses (for count-based benefits)
    
    # Status
    completed = Column(Integer, default=0)  # SQLite boolean: 1 = fully used
    completed_at = Column(String(26))
    
    # Manual tracking support
    manual_checked = Column(Integer, default=0)  # User manually marked as used
    manual_amount = Column(Float)  # User-entered amount for manual tracking
    manual_notes = Column(Text)
    
    # Reset tracking for one-time benefits
    reset_date = Column(String(10))  # When this benefit resets (for cardmember_year)
    
    # Timestamps
    created_at = Column(String(26), default=lambda: datetime.utcnow().isoformat())
    updated_at = Column(String(26), default=lambda: datetime.utcnow().isoformat(), onupdate=lambda: datetime.utcnow().isoformat())
    
    # Relationships
    user_card = relationship("UserCard", back_populates="benefit_periods")
