"""CSV parser service for transaction imports."""
import csv
import io
import json
import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.card import CardConfig
from app.models.transaction import Transaction


def parse_csv(
    db: Session,
    user_id: str,
    csv_content: str,
) -> dict:
    """Parse CSV content and import transactions.
    
    Returns dict with counts: imported, skipped (duplicates), errors.
    """
    reader = csv.DictReader(io.StringIO(csv_content))
    
    # Load card configs and their account patterns
    card_configs = db.query(CardConfig).all()
    card_patterns = []
    for cc in card_configs:
        patterns = json.loads(cc.account_patterns)
        for pattern in patterns:
            card_patterns.append((pattern.lower(), cc.id))
    
    imported = 0
    skipped = 0
    errors = []
    
    # Track keys seen in this import to handle duplicates within same file
    seen_in_file: set[tuple] = set()
    
    for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
        try:
            # Parse required fields
            date_str = row.get("date", "").strip().strip('"')
            name = row.get("name", "").strip().strip('"')
            amount_str = row.get("amount", "").strip().strip('"')
            account = row.get("account", "").strip().strip('"')
            
            if not date_str or not name or not amount_str or not account:
                errors.append(f"Row {row_num}: Missing required field")
                continue
            
            # Parse amount
            try:
                amount = float(amount_str)
            except ValueError:
                errors.append(f"Row {row_num}: Invalid amount '{amount_str}'")
                continue
            
            # Create dedup key
            dedup_key = (date_str, name, amount, account)
            
            # Check for duplicate within this file
            if dedup_key in seen_in_file:
                skipped += 1
                continue
            seen_in_file.add(dedup_key)
            
            # Match to card config
            card_config_id = None
            account_lower = account.lower()
            for pattern, config_id in card_patterns:
                if pattern in account_lower:
                    card_config_id = config_id
                    break
            
            # Check for duplicate in database
            existing = db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.date == date_str,
                Transaction.name == name,
                Transaction.amount == amount,
                Transaction.account == account,
            ).first()
            
            if existing:
                skipped += 1
                continue
            
            # Parse optional fields
            excluded_val = row.get("excluded", "").strip().lower()
            excluded = 1 if excluded_val in ("true", "1", "yes") else 0
            
            # Create transaction
            txn = Transaction(
                user_id=user_id,
                card_config_id=card_config_id,
                date=date_str,
                name=name,
                amount=amount,
                status=row.get("status", "").strip().strip('"') or None,
                category=row.get("category", "").strip().strip('"') or None,
                parent_category=row.get("parent category", "").strip().strip('"') or None,
                excluded=excluded,
                tags=row.get("tags", "").strip().strip('"') or None,
                type=row.get("type", "").strip().strip('"') or None,
                account=account,
                account_mask=row.get("account mask", "").strip().strip('"') or None,
                note=row.get("note", "").strip().strip('"') or None,
                recurring=row.get("recurring", "").strip().strip('"') or None,
            )
            db.add(txn)
            imported += 1
            
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
    
    db.commit()
    
    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors[:10],  # Limit error list
        "total_errors": len(errors),
    }


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
