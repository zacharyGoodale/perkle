"""Plaid integration API routes."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.item_remove_request import ItemRemoveRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.config import get_settings
from app.database import SessionLocal
from app.models.plaid_item import PlaidItem
from app.models.user import User
from app.schemas.plaid import (
    PlaidExchangeRequest,
    PlaidExchangeResponse,
    PlaidItemResponse,
    PlaidLinkTokenResponse,
    PlaidSyncResponse,
)
from app.services.benefit_detector import detect_benefits_for_user
from app.services.plaid_client import get_plaid_client
from app.services.plaid_sync import sync_plaid_transactions

router = APIRouter(prefix="/plaid", tags=["plaid"])


def _background_sync_and_detect(user_id: str):
    """Run sync + detect in a background task with its own DB session."""
    db = SessionLocal()
    try:
        sync_plaid_transactions(db, user_id)
        detect_benefits_for_user(db, user_id)
    finally:
        db.close()


def _require_plaid_configured():
    settings = get_settings()
    if not settings.plaid_client_id or not settings.plaid_secret:
        raise HTTPException(status_code=503, detail="Plaid integration not configured")


@router.post("/link-token", response_model=PlaidLinkTokenResponse)
def create_link_token(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a Plaid Link token for the frontend."""
    _require_plaid_configured()
    settings = get_settings()
    client = get_plaid_client()

    request = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(client_user_id=current_user.id),
        client_name=settings.app_name,
        products=[Products("transactions")],
        country_codes=[CountryCode("US")],
        language="en",
        redirect_uri=settings.plaid_redirect_uri or None,
    )
    response = client.link_token_create(request)

    return PlaidLinkTokenResponse(
        link_token=response.link_token,
        expiration=response.expiration.isoformat(),
    )


@router.post("/exchange", response_model=PlaidExchangeResponse)
def exchange_public_token(
    data: PlaidExchangeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Exchange a public token for an access token and store the Plaid item."""
    _require_plaid_configured()
    client = get_plaid_client()

    exchange_response = client.item_public_token_exchange(
        ItemPublicTokenExchangeRequest(public_token=data.public_token)
    )

    # Check for re-link of existing item
    existing = db.query(PlaidItem).filter(
        PlaidItem.item_id == exchange_response.item_id,
    ).first()
    if existing:
        existing.access_token = exchange_response.access_token
        existing.status = "active"
        existing.error_code = None
        db.commit()
    else:
        plaid_item = PlaidItem(
            user_id=current_user.id,
            item_id=exchange_response.item_id,
            access_token=exchange_response.access_token,
            institution_id=data.institution_id,
            institution_name=data.institution_name,
        )
        db.add(plaid_item)
        db.commit()

    # Sync + detect in background so the response returns immediately
    background_tasks.add_task(_background_sync_and_detect, current_user.id)

    institution_name = existing.institution_name if existing else data.institution_name
    return PlaidExchangeResponse(
        message="Account reconnected" if existing else "Account connected successfully",
        institution_name=institution_name,
    )


@router.post("/sync", response_model=PlaidSyncResponse)
def sync_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sync transactions from all connected Plaid accounts."""
    _require_plaid_configured()
    result = sync_plaid_transactions(db, current_user.id)
    detect_benefits_for_user(db, current_user.id)
    return PlaidSyncResponse(**result)


@router.get("/items", response_model=list[PlaidItemResponse])
def list_plaid_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all connected Plaid accounts for the current user."""
    items = db.query(PlaidItem).filter(
        PlaidItem.user_id == current_user.id,
    ).all()
    return items


@router.delete("/items/{item_id}")
def remove_plaid_item(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Disconnect a Plaid account."""
    plaid_item = db.query(PlaidItem).filter(
        PlaidItem.id == item_id,
        PlaidItem.user_id == current_user.id,
    ).first()
    if not plaid_item:
        raise HTTPException(status_code=404, detail="Plaid item not found")

    # Remove from Plaid
    try:
        _require_plaid_configured()
        client = get_plaid_client()
        client.item_remove(
            ItemRemoveRequest(access_token=plaid_item.access_token)
        )
    except HTTPException:
        raise
    except Exception:
        pass  # Still remove locally even if Plaid call fails

    db.delete(plaid_item)
    db.commit()
    return {"message": "Account disconnected"}
