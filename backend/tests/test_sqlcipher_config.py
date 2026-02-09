import importlib
import sys

import pytest


def reload_database_module():
    sys.modules.pop("app.database", None)
    config_module = sys.modules.get("app.config")
    if config_module:
        config_module.get_settings.cache_clear()
        sys.modules.pop("app.config", None)
    return importlib.import_module("app.database")


def test_sqlcipher_missing_key_fails_closed(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlcipher:///data/perkle.db")
    monkeypatch.setenv("DATABASE_KEY", "")

    with pytest.raises(ValueError, match="DATABASE_KEY must be set"):
        reload_database_module()


def test_sqlcipher_import_failure_fails_closed(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlcipher:///data/perkle.db")
    monkeypatch.setenv("DATABASE_KEY", "test-key")

    real_import_module = importlib.import_module

    def fake_import_module(name, package=None):
        if name == "pysqlcipher3":
            raise ImportError("boom")
        return real_import_module(name, package=package)

    monkeypatch.setattr(importlib, "import_module", fake_import_module)

    with pytest.raises(RuntimeError, match="pysqlcipher3 is required"):
        reload_database_module()
