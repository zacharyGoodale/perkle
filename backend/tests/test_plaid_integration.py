"""Tests for Plaid integration endpoints and sync service."""
import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_KEY", "test-db-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///./data/perkle.db")
os.environ.setdefault("SECRET_KEY", "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")
os.environ.setdefault("PLAID_CLIENT_ID", "test_client_id")
os.environ.setdefault("PLAID_SECRET", "test_secret")
os.environ.setdefault("PLAID_ENV", "sandbox")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.api import deps
from app.api.plaid import router as plaid_router
from app.database import Base
from app import models  # noqa: F401 — ensure all models registered with Base
from app.models.plaid_item import PlaidItem
from app.models.transaction import Transaction
from app.models.user import User


def _build_test_app():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = FastAPI()
    app.include_router(plaid_router, prefix="/api")

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Create a test user
    db = TestingSessionLocal()
    user = User(
        id="test-user-id",
        username="testuser",
        email="test@example.com",
        password_hash="hashed",
    )
    db.add(user)
    db.commit()
    db.close()

    def override_get_current_user():
        return User(
            id="test-user-id",
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
        )

    app.dependency_overrides[deps.get_db] = override_get_db
    app.dependency_overrides[deps.get_current_user] = override_get_current_user

    return TestClient(app), TestingSessionLocal


def _mock_link_token_response():
    mock = MagicMock()
    mock.link_token = "link-sandbox-test-token"
    mock.expiration = datetime(2026, 3, 7, 0, 0, 0)
    return mock


def _mock_exchange_response(item_id="item-sandbox-123", access_token="access-sandbox-456"):
    mock = MagicMock()
    mock.item_id = item_id
    mock.access_token = access_token
    return mock


@patch("app.api.plaid.get_plaid_client")
def test_create_link_token(mock_get_client):
    client, _ = _build_test_app()
    mock_plaid = MagicMock()
    mock_plaid.link_token_create.return_value = _mock_link_token_response()
    mock_get_client.return_value = mock_plaid

    response = client.post("/api/plaid/link-token")
    assert response.status_code == 200
    data = response.json()
    assert data["link_token"] == "link-sandbox-test-token"
    assert "expiration" in data


@patch("app.api.plaid.detect_benefits_for_user")
@patch("app.api.plaid.sync_plaid_transactions", return_value={"added": 0, "modified": 0, "removed": 0, "accounts_synced": 0})
@patch("app.api.plaid.get_plaid_client")
def test_exchange_creates_plaid_item(mock_get_client, mock_sync, mock_detect):
    client, SessionLocal = _build_test_app()
    mock_plaid = MagicMock()
    mock_plaid.item_public_token_exchange.return_value = _mock_exchange_response()
    mock_get_client.return_value = mock_plaid

    response = client.post("/api/plaid/exchange", json={
        "public_token": "public-sandbox-token",
        "institution_id": "ins_109508",
        "institution_name": "First Platypus Bank",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Account connected successfully"
    assert data["institution_name"] == "First Platypus Bank"

    # Verify item stored in DB
    db = SessionLocal()
    item = db.query(PlaidItem).filter(PlaidItem.user_id == "test-user-id").first()
    assert item is not None
    assert item.item_id == "item-sandbox-123"
    assert item.access_token == "access-sandbox-456"
    assert item.institution_name == "First Platypus Bank"
    assert item.status == "active"
    db.close()

    # Verify sync and detect were called
    mock_sync.assert_called_once()
    mock_detect.assert_called_once()


@patch("app.api.plaid.detect_benefits_for_user")
@patch("app.api.plaid.sync_plaid_transactions", return_value={"added": 0, "modified": 0, "removed": 0, "accounts_synced": 0})
@patch("app.api.plaid.get_plaid_client")
def test_exchange_reconnect_updates_token(mock_get_client, mock_sync, mock_detect):
    client, SessionLocal = _build_test_app()

    # Create an existing disconnected item
    db = SessionLocal()
    existing = PlaidItem(
        user_id="test-user-id",
        item_id="item-sandbox-123",
        access_token="old-access-token",
        institution_name="First Platypus Bank",
        status="disconnected",
        error_code="ITEM_LOGIN_REQUIRED",
    )
    db.add(existing)
    db.commit()
    db.close()

    mock_plaid = MagicMock()
    mock_plaid.item_public_token_exchange.return_value = _mock_exchange_response(
        access_token="new-access-token"
    )
    mock_get_client.return_value = mock_plaid

    response = client.post("/api/plaid/exchange", json={
        "public_token": "public-sandbox-relink",
    })
    assert response.status_code == 200
    assert response.json()["message"] == "Account reconnected"

    db = SessionLocal()
    item = db.query(PlaidItem).filter(PlaidItem.item_id == "item-sandbox-123").first()
    assert item.access_token == "new-access-token"
    assert item.status == "active"
    assert item.error_code is None
    db.close()


def test_list_plaid_items():
    client, SessionLocal = _build_test_app()

    db = SessionLocal()
    db.add(PlaidItem(
        user_id="test-user-id",
        item_id="item-1",
        access_token="access-1",
        institution_name="Bank A",
        status="active",
    ))
    db.add(PlaidItem(
        user_id="test-user-id",
        item_id="item-2",
        access_token="access-2",
        institution_name="Bank B",
        status="error",
        error_code="ITEM_LOGIN_REQUIRED",
    ))
    db.commit()
    db.close()

    response = client.get("/api/plaid/items")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2
    names = {i["institution_name"] for i in items}
    assert names == {"Bank A", "Bank B"}


@patch("app.api.plaid.get_plaid_client")
def test_remove_plaid_item(mock_get_client):
    client, SessionLocal = _build_test_app()
    mock_plaid = MagicMock()
    mock_get_client.return_value = mock_plaid

    db = SessionLocal()
    item = PlaidItem(
        id="item-uuid-1",
        user_id="test-user-id",
        item_id="item-sandbox-del",
        access_token="access-del",
        institution_name="Delete Me Bank",
    )
    db.add(item)
    db.commit()
    db.close()

    response = client.delete("/api/plaid/items/item-uuid-1")
    assert response.status_code == 200
    assert response.json()["message"] == "Account disconnected"

    db = SessionLocal()
    assert db.query(PlaidItem).filter(PlaidItem.id == "item-uuid-1").first() is None
    db.close()


def _mock_plaid_transaction(
    transaction_id="txn-1",
    date="2026-03-01",
    name="Coffee Shop",
    merchant_name="Starbucks",
    amount=5.50,
    account_id="acc-1",
    pending=False,
):
    txn = MagicMock()
    txn.transaction_id = transaction_id
    txn.date = date
    txn.name = name
    txn.merchant_name = merchant_name
    txn.amount = amount
    txn.account_id = account_id
    txn.pending = pending
    txn.personal_finance_category = MagicMock()
    txn.personal_finance_category.primary = "FOOD_AND_DRINK"
    txn.personal_finance_category.detailed = "FOOD_AND_DRINK_COFFEE"
    return txn


def _mock_plaid_account(account_id="acc-1", name="Platinum Card", mask="1234"):
    acc = MagicMock()
    acc.account_id = account_id
    acc.name = name
    acc.official_name = name
    acc.mask = mask
    return acc


@patch("app.services.plaid_sync.get_plaid_client")
def test_sync_adds_transactions(mock_get_client):
    from app.services.plaid_sync import sync_plaid_transactions

    _, SessionLocal = _build_test_app()
    mock_plaid = MagicMock()
    mock_get_client.return_value = mock_plaid

    # Setup: create a PlaidItem
    db = SessionLocal()
    db.add(PlaidItem(
        user_id="test-user-id",
        item_id="item-sync-1",
        access_token="access-sync-1",
        status="active",
    ))
    db.commit()

    # Mock accounts response
    acc_resp = MagicMock()
    acc_resp.accounts = [_mock_plaid_account()]
    mock_plaid.accounts_get.return_value = acc_resp

    # Mock sync response with one added transaction
    sync_resp = MagicMock()
    sync_resp.added = [_mock_plaid_transaction()]
    sync_resp.modified = []
    sync_resp.removed = []
    sync_resp.next_cursor = "cursor-1"
    sync_resp.has_more = False
    mock_plaid.transactions_sync.return_value = sync_resp

    result = sync_plaid_transactions(db, "test-user-id")
    assert result["added"] == 1
    assert result["modified"] == 0
    assert result["removed"] == 0

    # Verify transaction in DB
    txn = db.query(Transaction).filter(
        Transaction.plaid_transaction_id == "txn-1"
    ).first()
    assert txn is not None
    assert txn.name == "Starbucks"
    assert txn.amount == 5.50
    assert txn.source == "plaid"
    assert txn.status == "posted"
    assert txn.parent_category == "FOOD_AND_DRINK"

    # Verify cursor updated
    item = db.query(PlaidItem).filter(PlaidItem.item_id == "item-sync-1").first()
    assert item.cursor == "cursor-1"
    assert item.last_synced_at is not None

    db.close()


@patch("app.services.plaid_sync.get_plaid_client")
def test_sync_dedup_skips_existing(mock_get_client):
    from app.services.plaid_sync import sync_plaid_transactions

    _, SessionLocal = _build_test_app()
    mock_plaid = MagicMock()
    mock_get_client.return_value = mock_plaid

    db = SessionLocal()
    db.add(PlaidItem(
        user_id="test-user-id",
        item_id="item-dedup",
        access_token="access-dedup",
        status="active",
    ))
    # Pre-existing transaction
    db.add(Transaction(
        user_id="test-user-id",
        date="2026-03-01",
        name="Starbucks",
        amount=5.50,
        account="Platinum Card",
        source="plaid",
        plaid_transaction_id="txn-existing",
    ))
    db.commit()

    acc_resp = MagicMock()
    acc_resp.accounts = [_mock_plaid_account()]
    mock_plaid.accounts_get.return_value = acc_resp

    sync_resp = MagicMock()
    sync_resp.added = [_mock_plaid_transaction(transaction_id="txn-existing")]
    sync_resp.modified = []
    sync_resp.removed = []
    sync_resp.next_cursor = "cursor-2"
    sync_resp.has_more = False
    mock_plaid.transactions_sync.return_value = sync_resp

    result = sync_plaid_transactions(db, "test-user-id")
    assert result["added"] == 0  # Skipped because already exists

    count = db.query(Transaction).filter(
        Transaction.plaid_transaction_id == "txn-existing"
    ).count()
    assert count == 1  # Still only one row

    db.close()


@patch("app.services.plaid_sync.get_plaid_client")
def test_sync_removes_transactions(mock_get_client):
    from app.services.plaid_sync import sync_plaid_transactions

    _, SessionLocal = _build_test_app()
    mock_plaid = MagicMock()
    mock_get_client.return_value = mock_plaid

    db = SessionLocal()
    db.add(PlaidItem(
        user_id="test-user-id",
        item_id="item-remove",
        access_token="access-remove",
        status="active",
    ))
    db.add(Transaction(
        user_id="test-user-id",
        date="2026-03-01",
        name="Old Transaction",
        amount=10.00,
        account="Card",
        source="plaid",
        plaid_transaction_id="txn-to-remove",
    ))
    db.commit()

    acc_resp = MagicMock()
    acc_resp.accounts = []
    mock_plaid.accounts_get.return_value = acc_resp

    removed_txn = MagicMock()
    removed_txn.transaction_id = "txn-to-remove"

    sync_resp = MagicMock()
    sync_resp.added = []
    sync_resp.modified = []
    sync_resp.removed = [removed_txn]
    sync_resp.next_cursor = "cursor-3"
    sync_resp.has_more = False
    mock_plaid.transactions_sync.return_value = sync_resp

    result = sync_plaid_transactions(db, "test-user-id")
    assert result["removed"] == 1

    assert db.query(Transaction).filter(
        Transaction.plaid_transaction_id == "txn-to-remove"
    ).first() is None

    db.close()
