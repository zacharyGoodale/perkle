"""Notification model for benefit reminders."""
import uuid
from datetime import datetime

from sqlalchemy import Column, ForeignKey, Index, Integer, String, Text

from app.database import Base


class Notification(Base):
    """Notification for expiring or unused benefits."""
    
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_unread", "user_id", "read"),
        Index("ix_notifications_created", "user_id", "created_at"),
    )
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Notification type: benefit_expiring, benefit_unused, benefit_reset, system
    type = Column(String(50), nullable=False)
    
    # Context
    user_card_id = Column(String(36), ForeignKey("user_cards.id", ondelete="CASCADE"))
    benefit_slug = Column(String(50))
    benefit_period_id = Column(String(36), ForeignKey("benefit_periods.id", ondelete="CASCADE"))
    
    # Content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Status
    read = Column(Integer, default=0)  # SQLite boolean
    read_at = Column(String(26))
    dismissed = Column(Integer, default=0)  # SQLite boolean
    dismissed_at = Column(String(26))
    
    # Scheduling
    scheduled_for = Column(String(26))  # When to show notification
    expires_at = Column(String(26))  # When notification is no longer relevant
    
    # Timestamps
    created_at = Column(String(26), default=lambda: datetime.utcnow().isoformat())
