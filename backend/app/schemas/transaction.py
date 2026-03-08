"""Transaction schemas."""
from pydantic import BaseModel


class TransactionResponse(BaseModel):
    """Transaction response."""

    id: str
    date: str
    name: str
    amount: float
    status: str | None
    category: str | None
    parent_category: str | None
    account: str
    account_mask: str | None
    card_config_id: str | None
    benefit_slug: str | None
    source: str | None = None
    plaid_transaction_id: str | None = None
    imported_at: str

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Paginated transaction list response."""

    transactions: list[TransactionResponse]
    total: int
    limit: int
    offset: int
