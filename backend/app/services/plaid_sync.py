"""Plaid transaction sync service."""
from datetime import datetime

from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.plaid_item import PlaidItem
from app.models.transaction import Transaction
from app.services.card_matching import build_card_patterns, match_card_config
from app.services.plaid_client import get_plaid_client


def sync_plaid_transactions(db: Session, user_id: str) -> dict:
    """Sync transactions from all active Plaid items for a user.

    Uses /transactions/sync with cursor-based pagination.
    Returns counts of added, modified, removed transactions.
    """
    client = get_plaid_client()
    items = db.query(PlaidItem).filter(
        PlaidItem.user_id == user_id,
        PlaidItem.status == "active",
    ).all()

    card_patterns = build_card_patterns(db)
    total_added = 0
    total_modified = 0
    total_removed = 0

    for item in items:
        try:
            # Get account details for name/mask mapping
            accounts_response = client.accounts_get(
                AccountsGetRequest(access_token=item.access_token)
            )
            account_map = {a.account_id: a for a in accounts_response.accounts}

            cursor = item.cursor or ""
            has_more = True

            while has_more:
                response = client.transactions_sync(
                    TransactionsSyncRequest(
                        access_token=item.access_token,
                        cursor=cursor,
                    )
                )

                for txn in response.added:
                    if _upsert_plaid_transaction(db, user_id, txn, account_map, card_patterns):
                        total_added += 1

                for txn in response.modified:
                    if _update_plaid_transaction(db, user_id, txn, account_map):
                        total_modified += 1

                for removed_txn in response.removed:
                    if _remove_plaid_transaction(db, user_id, removed_txn.transaction_id):
                        total_removed += 1

                cursor = response.next_cursor
                has_more = response.has_more

            item.cursor = cursor
            item.last_synced_at = datetime.utcnow().isoformat()

        except Exception as e:
            error_code = getattr(e, "code", None) or str(type(e).__name__)
            item.status = "error"
            item.error_code = str(error_code)[:100]

    db.commit()
    return {
        "added": total_added,
        "modified": total_modified,
        "removed": total_removed,
        "accounts_synced": len(items),
    }


def _upsert_plaid_transaction(
    db: Session,
    user_id: str,
    txn,
    account_map: dict,
    card_patterns: list[tuple[str, str]],
) -> bool:
    """Insert a Plaid transaction if it doesn't already exist. Returns True if inserted."""
    existing = db.query(Transaction).filter(
        Transaction.plaid_transaction_id == txn.transaction_id,
        Transaction.user_id == user_id,
    ).first()
    if existing:
        return False

    account = account_map.get(txn.account_id)
    account_name = ""
    account_mask = None
    if account:
        account_name = account.official_name or account.name or ""
        account_mask = account.mask

    card_config_id = match_card_config(account_name, card_patterns)

    # Plaid personal_finance_category
    parent_category = None
    category = None
    if hasattr(txn, "personal_finance_category") and txn.personal_finance_category:
        parent_category = txn.personal_finance_category.primary
        category = txn.personal_finance_category.detailed

    transaction = Transaction(
        user_id=user_id,
        card_config_id=card_config_id,
        date=str(txn.date),
        name=txn.merchant_name or txn.name or "",
        amount=txn.amount,
        status="pending" if txn.pending else "posted",
        category=category,
        parent_category=parent_category,
        account=account_name,
        account_mask=account_mask,
        source="plaid",
        plaid_transaction_id=txn.transaction_id,
    )
    db.add(transaction)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return False
    return True


def _update_plaid_transaction(
    db: Session,
    user_id: str,
    txn,
    account_map: dict,
) -> bool:
    """Update an existing Plaid transaction. Returns True if updated."""
    existing = db.query(Transaction).filter(
        Transaction.plaid_transaction_id == txn.transaction_id,
        Transaction.user_id == user_id,
    ).first()
    if not existing:
        return False

    account = account_map.get(txn.account_id)
    if account:
        existing.account = account.official_name or account.name or existing.account
        existing.account_mask = account.mask or existing.account_mask

    existing.date = str(txn.date)
    existing.name = txn.merchant_name or txn.name or existing.name
    existing.amount = txn.amount
    existing.status = "pending" if txn.pending else "posted"

    if hasattr(txn, "personal_finance_category") and txn.personal_finance_category:
        existing.parent_category = txn.personal_finance_category.primary
        existing.category = txn.personal_finance_category.detailed

    return True


def _remove_plaid_transaction(db: Session, user_id: str, transaction_id: str) -> bool:
    """Remove a Plaid transaction. Returns True if removed."""
    existing = db.query(Transaction).filter(
        Transaction.plaid_transaction_id == transaction_id,
        Transaction.user_id == user_id,
    ).first()
    if not existing:
        return False
    db.delete(existing)
    return True
