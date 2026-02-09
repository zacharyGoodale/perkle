# Perkle Data Retention and Deletion SOP

## 1. Document Control

- Owner: Perkle engineering
- Version: 1.0
- Effective date: 2026-02-09
- Review cadence: At least annually and after schema/auth changes

## 2. Purpose

This SOP defines how Perkle handles:

- Data retention for user-related records
- User-requested data deletion (account deletion/right-to-delete requests)

This document is based on the current schema and application behavior in `backend/app/models/*` and `backend/app/api/*`.

## 3. Data Inventory and Retention Policy

### 3.1 User-Scoped Data Stored by the Application

- `users`: account profile + email + password hash + settings
- `user_cards`: cards user added
- `transactions`: uploaded transaction history
- `benefit_periods`: tracked benefit usage periods
- `user_benefit_settings`: muted/notes settings
- `notifications`: in-app notification history
- `refresh_sessions`: hashed refresh-token session records, user-agent, IP metadata

### 3.2 Non-User-Scoped Data

- `card_configs`: product card definitions loaded from YAML; retained as application configuration

### 3.3 Retention Rules (Current)

- Active accounts: User-scoped data is retained while account is active.
- Refresh tokens:
  - Token validity defaults to 7 days (`refresh_token_expire_days`), enforced in auth logic.
  - Session rows may remain in DB until explicit cleanup or account deletion.
- Deleted accounts: All user-scoped records are deleted via cascade from `users`.

## 4. Deletion Request Intake Procedure

1. Receive request through authenticated product/support channel.
2. Verify requester identity:
   - Preferred: request comes from authenticated user session.
   - If email/support based, verify control of the account email before processing.
3. Open an internal deletion ticket that records:
   - Request timestamp
   - Requester identity and account email
   - Operator handling the deletion
   - Completion timestamp and verification evidence

## 5. Account Deletion Runbook (Operational Procedure)

Perkle currently does not expose a public API endpoint for full account deletion. Deletion is executed by an operator using backend runtime access.

### 5.1 Optional Immediate Session Revocation

If user is currently authenticated, trigger logout flow to revoke active sessions:

- API route: `POST /api/auth/logout`
- Logic revokes active `refresh_sessions` for that user before deletion.

### 5.2 Execute Deletion by User Email (Docker deployment)

Run inside the backend container:

```bash
docker compose exec backend uv run python - <<'PY'
from app.database import SessionLocal
from app.models.user import User
from app.models.card import UserCard

target_email = "user@example.com"  # replace

db = SessionLocal()
try:
    user = db.query(User).filter(User.email == target_email).first()
    if not user:
        print("NOT_FOUND")
    else:
        user_id = user.id
        user_card_ids = [row[0] for row in db.query(UserCard.id).filter(UserCard.user_id == user_id).all()]
        print(f"TARGET user_id={user_id}")
        print(f"TARGET user_card_ids={user_card_ids}")
        db.delete(user)
        db.commit()
        print(f"DELETED user_id={user_id}")
finally:
    db.close()
PY
```

Why this works with current schema/model setup:

- `User` relationships are configured with `cascade="all, delete-orphan"` (`backend/app/models/user.py`).
- Foreign keys for user-owned records are configured with `ondelete="CASCADE"` in the schema/migrations.

### 5.3 Execute Deletion (local backend process)

If running locally (not Docker), use the same script from `backend/` with `uv run python`.

## 6. Post-Deletion Verification (Required)

After deletion, verify all user-scoped tables return zero rows for the deleted user.
Use the `user_id` and `user_card_ids` captured in step 5.2.

```bash
docker compose exec backend uv run python - <<'PY'
from app.database import SessionLocal
from app.models.user import User
from app.models.card import UserCard, UserBenefitSettings
from app.models.transaction import Transaction
from app.models.benefit import BenefitPeriod
from app.models.notification import Notification
from app.models.auth import RefreshSession

deleted_user_id = "replace-with-user-id-from-step-5-2"
deleted_user_card_ids = ["replace-with-card-id-from-step-5-2"]

db = SessionLocal()
try:
    print("users:", db.query(User).filter(User.id == deleted_user_id).count())
    print("user_cards:", db.query(UserCard).filter(UserCard.user_id == deleted_user_id).count())
    print("transactions:", db.query(Transaction).filter(Transaction.user_id == deleted_user_id).count())
    print("user_benefit_settings:", db.query(UserBenefitSettings).filter(UserBenefitSettings.user_id == deleted_user_id).count())
    print("notifications:", db.query(Notification).filter(Notification.user_id == deleted_user_id).count())
    print("refresh_sessions:", db.query(RefreshSession).filter(RefreshSession.user_id == deleted_user_id).count())
    if deleted_user_card_ids and deleted_user_card_ids[0] != "replace-with-card-id-from-step-5-2":
        print("benefit_periods:", db.query(BenefitPeriod).filter(BenefitPeriod.user_card_id.in_(deleted_user_card_ids)).count())
finally:
    db.close()
PY
```

Expected result after a successful deletion: all printed counts are `0`.

Record verification output in the deletion ticket.

## 7. Backups and Residual Copies

- If a database backup exists that contains deleted user data, mark that backup for deletion according to internal legal/compliance retention requirements.
- If backup deletion is not immediately possible, document:
  - Backup location
  - Planned purge date
  - Reason for temporary retention

## 8. SLA and Legal Handling

- Process deletion requests within required legal timelines for applicable jurisdictions.
- If a request cannot be fully completed (e.g., legal hold), document legal basis and notify requester as required.

## 9. Periodic Review

Review this SOP when:

- User schema changes (new user-linked tables/fields)
- Auth/session architecture changes
- Deployment/storage architecture changes (backup/encryption changes)

At review time, validate the runbook commands still match the live code paths and model relationships.
