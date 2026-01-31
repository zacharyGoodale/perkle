"""Card-related models."""
import uuid
from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class CardConfig(Base):
    """Credit card configuration (seeded from YAML files)."""
    
    __tablename__ = "card_configs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slug = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    issuer = Column(String(50), nullable=False)
    annual_fee = Column(Integer, default=0)
    benefits_url = Column(String(255))  # Link to official benefits page
    account_patterns = Column(Text, nullable=False)  # JSON array
    benefits = Column(Text, nullable=False)  # JSON array of benefit configs
    created_at = Column(String(26), default=lambda: datetime.utcnow().isoformat())
    updated_at = Column(String(26), default=lambda: datetime.utcnow().isoformat(), onupdate=lambda: datetime.utcnow().isoformat())
    
    # Relationships
    user_cards = relationship("UserCard", back_populates="card_config")
    transactions = relationship("Transaction", back_populates="card_config")


class UserCard(Base):
    """User's card in their portfolio."""
    
    __tablename__ = "user_cards"
    __table_args__ = (
        UniqueConstraint("user_id", "card_config_id", name="uq_user_card"),
    )
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    card_config_id = Column(String(36), ForeignKey("card_configs.id"), nullable=False)
    nickname = Column(String(100))
    card_anniversary = Column(String(10))  # YYYY-MM-DD for cardmember_year benefits
    active = Column(Integer, default=1)  # SQLite boolean
    added_at = Column(String(26), default=lambda: datetime.utcnow().isoformat())
    
    # Relationships
    user = relationship("User", back_populates="user_cards")
    card_config = relationship("CardConfig", back_populates="user_cards")
    benefit_periods = relationship("BenefitPeriod", back_populates="user_card", cascade="all, delete-orphan")
    benefit_settings = relationship("UserBenefitSettings", back_populates="user_card", cascade="all, delete-orphan")


class UserBenefitSettings(Base):
    """User-specific settings for benefits (muting, notes)."""
    
    __tablename__ = "user_benefit_settings"
    __table_args__ = (
        UniqueConstraint("user_id", "user_card_id", "benefit_slug", name="uq_user_benefit_setting"),
    )
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_card_id = Column(String(36), ForeignKey("user_cards.id", ondelete="CASCADE"), nullable=False, index=True)
    benefit_slug = Column(String(50), nullable=False)
    muted = Column(Integer, default=0)  # SQLite boolean: 1 = muted
    muted_at = Column(String(26))
    notes = Column(Text)  # User's personal notes
    created_at = Column(String(26), default=lambda: datetime.utcnow().isoformat())
    updated_at = Column(String(26), default=lambda: datetime.utcnow().isoformat(), onupdate=lambda: datetime.utcnow().isoformat())
    
    # Relationships
    user = relationship("User", back_populates="benefit_settings")
    user_card = relationship("UserCard", back_populates="benefit_settings")
