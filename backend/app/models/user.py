"""User model."""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """User account."""
    
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    settings = Column(Text, default="{}")  # JSON for notification prefs, etc.
    created_at = Column(String(26), default=lambda: datetime.utcnow().isoformat())
    updated_at = Column(String(26), default=lambda: datetime.utcnow().isoformat(), onupdate=lambda: datetime.utcnow().isoformat())
    
    # Relationships
    user_cards = relationship("UserCard", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", backref="user", cascade="all, delete-orphan")
    benefit_settings = relationship("UserBenefitSettings", back_populates="user", cascade="all, delete-orphan")
