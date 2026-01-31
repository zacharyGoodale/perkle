"""Notification service for benefit reminders and card renewal alerts."""
import json
import os
import smtplib
from datetime import date, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from app.models.card import UserCard
from app.models.notification import Notification
from app.models.user import User
from app.services.benefit_detector import get_benefit_status_for_user


def get_expiring_benefits_for_user(
    db: Session,
    user_id: str,
    days_threshold: int = 7,
) -> list[dict]:
    """Get benefits expiring within the threshold days."""
    status = get_benefit_status_for_user(db, user_id, include_muted=False)
    
    expiring = []
    for card in status:
        for benefit in card["benefits"]:
            if benefit["status"] == "expiring" or (
                benefit["status"] in ("available", "partial") 
                and benefit["days_remaining"] <= days_threshold
                and benefit["days_remaining"] > 0
            ):
                expiring.append({
                    "card_name": card["card_name"],
                    "benefit_name": benefit["name"],
                    "value": benefit["value"],
                    "amount_used": benefit["amount_used"],
                    "days_remaining": benefit["days_remaining"],
                    "period_end": benefit["period_end"],
                })
    
    return expiring


def get_upcoming_renewals(
    db: Session,
    user_id: str,
    days_threshold: int = 30,
) -> list[dict]:
    """Get cards with annual fees renewing within threshold days."""
    status = get_benefit_status_for_user(db, user_id, include_muted=True)
    
    renewals = []
    for card in status:
        if card["days_until_renewal"] and card["days_until_renewal"] <= days_threshold:
            renewals.append({
                "card_name": card["card_name"],
                "annual_fee": card["annual_fee"],
                "days_until_renewal": card["days_until_renewal"],
                "anniversary": card["card_anniversary"],
            })
    
    return renewals


def create_notification(
    db: Session,
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    user_card_id: str | None = None,
    benefit_slug: str | None = None,
    expires_at: str | None = None,
) -> Notification:
    """Create an in-app notification."""
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        user_card_id=user_card_id,
        benefit_slug=benefit_slug,
        expires_at=expires_at,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def send_email_notification(
    to_email: str,
    subject: str,
    html_content: str,
) -> bool:
    """Send an email notification using SMTP.
    
    Requires environment variables:
    - SMTP_HOST
    - SMTP_PORT (default 587)
    - SMTP_USER
    - SMTP_PASSWORD
    - SMTP_FROM_EMAIL
    """
    smtp_host = os.getenv("SMTP_HOST")
    if not smtp_host:
        print("SMTP not configured, skipping email")
        return False
    
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    from_email = os.getenv("SMTP_FROM_EMAIL", "noreply@perkle.app")
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    
    # Plain text fallback
    plain_text = html_content.replace("<br>", "\n").replace("</p>", "\n\n")
    # Strip remaining HTML tags
    import re
    plain_text = re.sub(r"<[^>]+>", "", plain_text)
    
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_content, "html"))
    
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def generate_weekly_digest_html(
    user: User,
    expiring_benefits: list[dict],
    upcoming_renewals: list[dict],
) -> str:
    """Generate HTML content for weekly digest email."""
    html = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #1e40af;">🎯 Perkle Weekly Digest</h1>
        <p>Hi {user.username},</p>
        <p>Here's your weekly summary of credit card benefits to use before they expire.</p>
    """
    
    if expiring_benefits:
        html += """
        <h2 style="color: #ea580c; margin-top: 24px;">⏰ Benefits Expiring Soon</h2>
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="background: #f3f4f6;">
                <th style="padding: 8px; text-align: left;">Card</th>
                <th style="padding: 8px; text-align: left;">Benefit</th>
                <th style="padding: 8px; text-align: right;">Remaining</th>
                <th style="padding: 8px; text-align: right;">Days</th>
            </tr>
        """
        for b in expiring_benefits:
            remaining = b["value"] - b["amount_used"]
            html += f"""
            <tr style="border-bottom: 1px solid #e5e7eb;">
                <td style="padding: 8px;">{b['card_name']}</td>
                <td style="padding: 8px;">{b['benefit_name']}</td>
                <td style="padding: 8px; text-align: right;">${remaining:.0f}</td>
                <td style="padding: 8px; text-align: right; color: #ea580c;">{b['days_remaining']}d</td>
            </tr>
            """
        html += "</table>"
    else:
        html += "<p style='color: #16a34a;'>✅ No benefits expiring in the next 7 days!</p>"
    
    if upcoming_renewals:
        html += """
        <h2 style="color: #d97706; margin-top: 24px;">💳 Upcoming Annual Fee Renewals</h2>
        """
        for r in upcoming_renewals:
            html += f"""
            <p style="padding: 12px; background: #fffbeb; border-radius: 8px; margin: 8px 0;">
                <strong>{r['card_name']}</strong><br>
                ${r['annual_fee']} due in {r['days_until_renewal']} days
                {f" ({r['anniversary']})" if r['anniversary'] else ""}
            </p>
            """
    
    html += """
        <p style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 12px;">
            You're receiving this because you have notifications enabled in Perkle.
        </p>
    </body>
    </html>
    """
    
    return html


def send_weekly_digest_for_user(db: Session, user: User) -> bool:
    """Send weekly digest email to a user if they have expiring benefits."""
    # Get user notification preferences
    settings = json.loads(user.settings or "{}")
    if not settings.get("email_notifications", True):
        return False
    
    expiring = get_expiring_benefits_for_user(db, user.id, days_threshold=7)
    renewals = get_upcoming_renewals(db, user.id, days_threshold=30)
    
    # Only send if there's something to report
    if not expiring and not renewals:
        return False
    
    html = generate_weekly_digest_html(user, expiring, renewals)
    
    subject = "🎯 Perkle: "
    if expiring:
        subject += f"{len(expiring)} benefits expiring soon"
    if renewals:
        if expiring:
            subject += " + "
        subject += f"{len(renewals)} card renewals"
    
    return send_email_notification(user.email, subject, html)


def send_all_weekly_digests(db: Session) -> dict:
    """Send weekly digest to all users. Call this from a scheduler/cron."""
    users = db.query(User).all()
    
    sent = 0
    skipped = 0
    failed = 0
    
    for user in users:
        try:
            if send_weekly_digest_for_user(db, user):
                sent += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"Failed to send digest to {user.email}: {e}")
            failed += 1
    
    return {"sent": sent, "skipped": skipped, "failed": failed}
