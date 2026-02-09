import importlib
import os
import sys

import pytest

os.environ.setdefault("SECRET_KEY", "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")


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


def test_build_sqlcipher_url_injects_encoded_password(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./data/perkle.db")
    monkeypatch.setenv("DATABASE_KEY", "test-key")

    database_module = reload_database_module()
    rewritten_url = database_module._build_sqlcipher_url(
        "sqlite+pysqlcipher:///data/perkle.db?kdf_iter=64000",
        "test/key with space",
    )

    assert rewritten_url == (
        "sqlite+pysqlcipher://:test%2Fkey%20with%20space@/data/perkle.db?kdf_iter=64000"
    )


def test_build_sqlcipher_url_preserves_existing_password(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./data/perkle.db")
    monkeypatch.setenv("DATABASE_KEY", "test-key")

    database_module = reload_database_module()
    rewritten_url = database_module._build_sqlcipher_url(
        "sqlite+pysqlcipher://:already-set@/data/perkle.db",
        "new-key",
    )

    assert rewritten_url == "sqlite+pysqlcipher://:already-set@/data/perkle.db"
