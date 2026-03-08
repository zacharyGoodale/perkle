"""Transactions API endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import (
    TransactionListResponse,
    TransactionResponse,
)
from app.services.card_matching import get_user_transactions

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    card_config_id: str | None = Query(None, description="Filter by card"),
    start_date: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    credits_only: bool = Query(False, description="Only show credits (negative amounts)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List transactions with optional filters."""
    transactions = get_user_transactions(
        db,
        current_user.id,
        card_config_id=card_config_id,
        start_date=start_date,
        end_date=end_date,
        credits_only=credits_only,
        limit=limit,
        offset=offset,
    )

    # Get total count
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    if card_config_id:
        query = query.filter(Transaction.card_config_id == card_config_id)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    if credits_only:
        query = query.filter(Transaction.amount < 0)
    total = query.count()

    return TransactionListResponse(
        transactions=[TransactionResponse.model_validate(t) for t in transactions],
        total=total,
        limit=limit,
        offset=offset,
    )
