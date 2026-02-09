import importlib
import sys

import pytest


def reload_config_module():
    config_module = sys.modules.get("app.config")
    if config_module:
        config_module.get_settings.cache_clear()
        sys.modules.pop("app.config", None)
    return importlib.import_module("app.config")


def test_missing_secret_key_fails_closed(monkeypatch):
    monkeypatch.setenv("DATABASE_KEY", "test-db-key")
    monkeypatch.setenv("SECRET_KEY", "")

    config_module = reload_config_module()
    config_module.get_settings.cache_clear()

    with pytest.raises(Exception, match="secret_key|SECRET_KEY"):
        config_module.get_settings()


def test_weak_secret_key_fails_closed(monkeypatch):
    monkeypatch.setenv("DATABASE_KEY", "test-db-key")
    monkeypatch.setenv("SECRET_KEY", "changeme-in-production")

    config_module = reload_config_module()
    config_module.get_settings.cache_clear()

    with pytest.raises(Exception, match="secret_key|SECRET_KEY"):
        config_module.get_settings()


def test_strong_secret_key_passes(monkeypatch):
    monkeypatch.setenv("DATABASE_KEY", "test-db-key")
    monkeypatch.setenv(
        "SECRET_KEY",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    )

    config_module = reload_config_module()
    config_module.get_settings.cache_clear()
    settings = config_module.get_settings()

    assert settings.secret_key
