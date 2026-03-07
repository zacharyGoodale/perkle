"""Plaid API client singleton."""
from functools import lru_cache

import plaid
from plaid.api import plaid_api

from app.config import get_settings

_ENV_MAP = {
    "sandbox": plaid.Environment.Sandbox,
    "production": plaid.Environment.Production,
}


@lru_cache
def get_plaid_client() -> plaid_api.PlaidApi:
    """Get cached Plaid API client configured from settings."""
    settings = get_settings()
    configuration = plaid.Configuration(
        host=_ENV_MAP[settings.plaid_env],
        api_key={
            "clientId": settings.plaid_client_id,
            "secret": settings.plaid_secret,
        },
    )
    api_client = plaid.ApiClient(configuration)
    return plaid_api.PlaidApi(api_client)
