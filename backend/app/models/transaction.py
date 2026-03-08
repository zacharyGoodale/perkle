"""Transaction model."""
import uuid
from datetime import datetime

from sqlalchemy import Column, Float, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Transaction(Base):
    """Transaction record."""
    
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("user_id", "date", "name", "amount", "account", name="uq_transaction"),
        Index("ix_transactions_user_date", "user_id", "date"),
        Index("ix_transactions_category", "user_id", "category"),
    )
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    card_config_id = Column(String(36), ForeignKey("card_configs.id"))  # Matched via account patterns
    
    # Core transaction fields
    date = Column(String(10), nullable=False)  # YYYY-MM-DD
    name = Column(String(255), nullable=False)  # Merchant name
    amount = Column(Float, nullable=False)  # Positive = spend, negative = credit
    status = Column(String(50))
    
    # Categorization
    category = Column(String(100))
    parent_category = Column(String(100))
    
    # Additional fields
    account = Column(String(100), nullable=False)  # Account name for matching
    account_mask = Column(String(20))  # Last 4 digits
    
    # Benefit tracking
    benefit_slug = Column(String(50))  # Which benefit this applies to (if any)

    # Source tracking
    source = Column(String(10), default="plaid")  # "csv" or "plaid"
    plaid_transaction_id = Column(String(100), index=True)
    
    # Timestamps
    imported_at = Column(String(26), default=lambda: datetime.utcnow().isoformat())
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    card_config = relationship("CardConfig", back_populates="transactions")
