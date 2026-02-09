"""Authentication API endpoints."""
from datetime import datetime, timedelta
import hashlib
import uuid

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.config import get_settings
from app.models.auth import RefreshSession
from app.models.user import User
from app.schemas.auth import (
    MessageResponse,
    Token,
    UserLogin,
    UserRegister,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = to_encode.pop("exp", datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days))
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def hash_token_id(token_id: str) -> str:
    """Hash refresh token identifier before persisting."""
    return hashlib.sha256(token_id.encode("utf-8")).hexdigest()


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Issue secure HttpOnly refresh-token cookie."""
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path=settings.refresh_cookie_path,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
    )


def clear_refresh_cookie(response: Response) -> None:
    """Clear refresh-token cookie."""
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path=settings.refresh_cookie_path,
        secure=settings.refresh_cookie_secure,
        httponly=True,
        samesite=settings.refresh_cookie_samesite,
    )


def get_request_ip(request: Request) -> str | None:
    """Extract best-effort client IP for session metadata."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def create_refresh_session(
    db: Session,
    user_id: str,
    request: Request,
    rotated_from_id: str | None = None,
) -> tuple[RefreshSession, str]:
    """Create persisted refresh session + JWT pair."""
    jti = str(uuid.uuid4())
    expires_at_dt = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)

    session = RefreshSession(
        user_id=user_id,
        jti_hash=hash_token_id(jti),
        expires_at=expires_at_dt.isoformat(),
        rotated_from_id=rotated_from_id,
        user_agent=request.headers.get("user-agent"),
        ip_address=get_request_ip(request),
    )
    db.add(session)
    db.flush()

    refresh_token = create_refresh_token({"sub": user_id, "jti": jti, "exp": expires_at_dt})
    return session, refresh_token


def revoke_all_user_sessions(db: Session, user_id: str) -> None:
    """Revoke all active refresh sessions for a user."""
    now = datetime.utcnow().isoformat()
    db.query(RefreshSession).filter(
        RefreshSession.user_id == user_id,
        RefreshSession.revoked_at.is_(None),
    ).update(
        {"revoked_at": now, "last_used_at": now},
        synchronize_session=False,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check username
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    # Check email
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/login", response_model=Token)
def login(
    user_data: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Login and get tokens."""
    # Find user by username or email
    user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.username)
    ).first()
    
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    token_data = {"sub": user.id}
    access_token = create_access_token(token_data)
    _, refresh_token = create_refresh_session(db, user.id, request)
    db.commit()
    set_refresh_cookie(response, refresh_token)
    
    return Token(access_token=access_token)


@router.post("/refresh", response_model=Token)
def refresh_tokens(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Refresh access token using secure cookie refresh token."""
    refresh_cookie = request.cookies.get(settings.refresh_cookie_name)
    if not refresh_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )

    try:
        payload = jwt.decode(
            refresh_cookie,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        
        user_id: str = payload.get("sub")
        jti: str | None = payload.get("jti")
        if user_id is None or jti is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
    except JWTError:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    session = db.query(RefreshSession).filter(
        RefreshSession.user_id == user_id,
        RefreshSession.jti_hash == hash_token_id(jti),
    ).first()
    if not session or session.revoked_at:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh session",
        )

    try:
        expires_at = datetime.fromisoformat(session.expires_at)
    except ValueError:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh session",
        )
    if expires_at <= datetime.utcnow():
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh session expired",
        )

    # Verify user still exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    now = datetime.utcnow().isoformat()
    session.revoked_at = now
    session.last_used_at = now
    _, new_refresh_token = create_refresh_session(db, user.id, request, rotated_from_id=session.id)

    # Create new access token
    access_token = create_access_token({"sub": user.id})
    db.commit()
    set_refresh_cookie(response, new_refresh_token)

    return Token(access_token=access_token)


@router.post("/logout", response_model=MessageResponse)
def logout(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Logout and revoke all refresh sessions for the current user."""
    revoke_all_user_sessions(db, current_user.id)
    db.commit()
    clear_refresh_cookie(response)
    return MessageResponse(message="Successfully logged out")
