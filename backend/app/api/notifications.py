"""Notification API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.notification import Notification
from app.models.user import User
from app.services.notifications import (
    get_expiring_benefits_for_user,
    get_upcoming_renewals,
    send_weekly_digest_for_user,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    read: bool
    created_at: str

    class Config:
        from_attributes = True


class DigestPreviewResponse(BaseModel):
    expiring_benefits: list[dict]
    upcoming_renewals: list[dict]


class SendDigestResponse(BaseModel):
    sent: bool
    message: str


@router.get("", response_model=list[NotificationResponse])
def get_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user's notifications."""
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.read == 0)
    
    notifications = query.order_by(Notification.created_at.desc()).limit(50).all()
    return [
        NotificationResponse(
            id=n.id,
            type=n.type,
            title=n.title,
            message=n.message,
            read=bool(n.read),
            created_at=n.created_at,
        )
        for n in notifications
    ]


@router.post("/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a notification as read."""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.read = 1
    db.commit()
    return {"success": True}


@router.get("/digest/preview", response_model=DigestPreviewResponse)
def preview_digest(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Preview what would be in your weekly digest email."""
    return DigestPreviewResponse(
        expiring_benefits=get_expiring_benefits_for_user(db, current_user.id, days_threshold=7),
        upcoming_renewals=get_upcoming_renewals(db, current_user.id, days_threshold=30),
    )


@router.post("/digest/send", response_model=SendDigestResponse)
def send_digest_now(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send your weekly digest email now (for testing)."""
    sent = send_weekly_digest_for_user(db, current_user)
    if sent:
        return SendDigestResponse(sent=True, message="Digest email sent")
    return SendDigestResponse(sent=False, message="No digest sent (nothing to report or email disabled)")
