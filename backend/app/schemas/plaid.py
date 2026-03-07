"""Plaid schemas."""
from pydantic import BaseModel


class PlaidLinkTokenResponse(BaseModel):
    link_token: str
    expiration: str


class PlaidExchangeRequest(BaseModel):
    public_token: str
    institution_id: str | None = None
    institution_name: str | None = None


class PlaidExchangeResponse(BaseModel):
    message: str
    institution_name: str | None = None


class PlaidSyncResponse(BaseModel):
    added: int
    modified: int
    removed: int
    accounts_synced: int


class PlaidItemResponse(BaseModel):
    id: str
    institution_name: str | None
    status: str
    last_synced_at: str | None
    created_at: str

    class Config:
        from_attributes = True
