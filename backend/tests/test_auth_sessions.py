import os
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_KEY", "test-db-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///./data/perkle.db")
os.environ.setdefault("SECRET_KEY", "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.api import deps
from app.api.auth import router as auth_router
from app.database import Base
from app.models.auth import RefreshSession


def _cookie_value(set_cookie_header: str, cookie_name: str) -> str:
    token_part = set_cookie_header.split(";", 1)[0]
    name, value = token_part.split("=", 1)
    assert name == cookie_name
    return value


def _build_test_client():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = FastAPI()
    app.include_router(auth_router, prefix="/api")

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[deps.get_db] = override_get_db
    return TestClient(app), TestingSessionLocal


def _register_and_login(client: TestClient, username: str, email: str):
    register_response = client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": "TestPass123!"},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "TestPass123!"},
    )
    assert login_response.status_code == 200
    return login_response


def test_login_sets_secure_httponly_refresh_cookie():
    client, _ = _build_test_client()

    login_response = _register_and_login(client, "alpha", "alpha@example.com")
    data = login_response.json()
    set_cookie = login_response.headers.get("set-cookie", "")

    assert "access_token" in data
    assert "refresh_token" not in data
    assert "perkle_refresh=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "Secure" in set_cookie
    assert "samesite=lax" in set_cookie.lower()


def test_refresh_rotates_session_and_rejects_replay():
    client, _ = _build_test_client()

    login_response = _register_and_login(client, "beta", "beta@example.com")
    old_cookie = _cookie_value(login_response.headers["set-cookie"], "perkle_refresh")

    refresh_response = client.post(
        "/api/auth/refresh",
        headers={"Cookie": f"perkle_refresh={old_cookie}"},
    )
    assert refresh_response.status_code == 200
    new_cookie = _cookie_value(refresh_response.headers["set-cookie"], "perkle_refresh")
    assert new_cookie != old_cookie

    replay_response = client.post(
        "/api/auth/refresh",
        headers={"Cookie": f"perkle_refresh={old_cookie}"},
    )
    assert replay_response.status_code == 401


def test_logout_revokes_all_refresh_sessions():
    client, testing_session_local = _build_test_client()

    first_login = _register_and_login(client, "gamma", "gamma@example.com")
    first_access_token = first_login.json()["access_token"]
    second_login = client.post(
        "/api/auth/login",
        json={"username": "gamma", "password": "TestPass123!"},
    )
    assert second_login.status_code == 200
    second_cookie = _cookie_value(second_login.headers["set-cookie"], "perkle_refresh")

    logout_response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {first_access_token}"},
    )
    assert logout_response.status_code == 200

    refresh_after_logout = client.post(
        "/api/auth/refresh",
        headers={"Cookie": f"perkle_refresh={second_cookie}"},
    )
    assert refresh_after_logout.status_code == 401

    db = testing_session_local()
    try:
        active_sessions = db.query(RefreshSession).filter(RefreshSession.revoked_at.is_(None)).count()
        assert active_sessions == 0
    finally:
        db.close()
