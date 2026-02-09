"""Authentication/session models."""
import uuid
from datetime import datetime

from sqlalchemy import Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.database import Base


class RefreshSession(Base):
    """Tracks refresh-token sessions for rotation and revocation."""

    __tablename__ = "refresh_sessions"
    __table_args__ = (
        Index("ix_refresh_sessions_user_active", "user_id", "revoked_at"),
        Index("ix_refresh_sessions_expires_at", "expires_at"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    jti_hash = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(String(26), default=lambda: datetime.utcnow().isoformat())
    expires_at = Column(String(26), nullable=False)
    revoked_at = Column(String(26))
    last_used_at = Column(String(26))
    rotated_from_id = Column(String(36), ForeignKey("refresh_sessions.id", ondelete="SET NULL"))
    user_agent = Column(String(255))
    ip_address = Column(String(45))

    user = relationship("User", back_populates="refresh_sessions")
