"""Plaid Item model for linked bank accounts."""
import uuid
from datetime import datetime

from sqlalchemy import Column, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class PlaidItem(Base):
    """A linked Plaid institution for a user."""

    __tablename__ = "plaid_items"
    __table_args__ = (
        UniqueConstraint("user_id", "item_id", name="uq_plaid_item"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(String(100), nullable=False, unique=True)
    access_token = Column(String(255), nullable=False)
    institution_id = Column(String(50))
    institution_name = Column(String(255))
    cursor = Column(Text)  # /transactions/sync cursor for incremental sync
    status = Column(String(20), default="active")  # active, error, disconnected
    error_code = Column(String(100))
    last_synced_at = Column(String(26))
    created_at = Column(String(26), default=lambda: datetime.utcnow().isoformat())

    user = relationship("User", back_populates="plaid_items")
