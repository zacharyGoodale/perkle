"""Card matching utilities for transaction processing."""
import json

from sqlalchemy.orm import Session

from app.models.card import CardConfig
from app.models.transaction import Transaction


def build_card_patterns(db: Session) -> list[tuple[str, str]]:
    """Load card configs and build (pattern, config_id) pairs for account matching."""
    card_configs = db.query(CardConfig).all()
    patterns = []
    for cc in card_configs:
        for pattern in json.loads(cc.account_patterns):
            patterns.append((pattern.lower(), cc.id))
    return patterns


def match_card_config(account_name: str, card_patterns: list[tuple[str, str]]) -> str | None:
    """Match an account name to a card config ID using account patterns."""
    account_lower = account_name.lower()
    for pattern, config_id in card_patterns:
        if pattern in account_lower:
            return config_id
    return None


def get_user_transactions(
    db: Session,
    user_id: str,
    card_config_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    credits_only: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> list[Transaction]:
    """Get transactions for a user with optional filters."""
    query = db.query(Transaction).filter(Transaction.user_id == user_id)

    if card_config_id:
        query = query.filter(Transaction.card_config_id == card_config_id)

    if start_date:
        query = query.filter(Transaction.date >= start_date)

    if end_date:
        query = query.filter(Transaction.date <= end_date)

    if credits_only:
        query = query.filter(Transaction.amount < 0)

    return query.order_by(Transaction.date.desc()).offset(offset).limit(limit).all()
