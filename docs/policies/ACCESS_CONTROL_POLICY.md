# Perkle Access Control Policy

## 1. Document Control

- Owner: Perkle engineering
- Version: 1.0
- Effective date: 2026-02-09
- Review cadence: At least annually and after authentication/authorization changes

## 2. Purpose

This policy defines how access to Perkle systems and user data is authenticated, authorized, and revoked based on the current implementation.

## 3. Scope

This policy applies to:

- API authentication and route protection (`backend/app/api/auth.py`, `backend/app/api/deps.py`)
- Session/token handling (`backend/app/models/auth.py`, `frontend/src/lib/api.ts`, `frontend/src/context/AuthContext.tsx`)
- Database-level user data ownership checks in API handlers
- Deployment-time secret management related to access control (`backend/app/config.py`, `docker-compose.yml`, `deploy.sh`)

## 4. Access Control Model

Perkle uses account-based authentication with token-based API access:

- Users authenticate with username/email and password.
- Passwords are stored using bcrypt hashing.
- API access uses short-lived bearer access tokens (JWT).
- Session continuity uses refresh tokens in secure HttpOnly cookies.
- Refresh sessions are persisted server-side and rotated on refresh.

Perkle currently uses application-level ownership checks (row-level filters by `current_user.id`) for user data access.

## 5. Authentication Controls (Implemented)

- Password hashing: bcrypt (`backend/app/api/auth.py`).
- Secret strength enforcement: `SECRET_KEY` must meet minimum length and entropy checks, weak values fail closed (`backend/app/config.py`).
- Access token TTL: default 15 minutes (`backend/app/config.py`).
- Refresh token TTL: default 7 days (`backend/app/config.py`).
- Refresh token transport:
  - Stored in `HttpOnly` cookie
  - `Secure` flag enabled by default
  - `SameSite=Lax`
  - Cookie path restricted to `/api/auth`
- Deployment access layer (current production model):
  - Perkle is deployed behind Tailscale.
  - Access to the app is gated by Tailscale identity and device controls, including MFA where configured in the organization IdP/Tailnet policy.

## 6. Authorization Controls (Implemented)

- Protected routes require valid access token (`backend/app/api/deps.py`).
- Token type is validated (`access` required for API authorization).
- For user-scoped resources, endpoints enforce ownership by filtering on `current_user.id` before read/update/delete operations (cards, transactions, benefits, notifications).
- User not found/ownership failures return authorization errors or not-found responses.

## 7. Session Management and Revocation

- Refresh sessions are recorded in `refresh_sessions` with hashed token IDs (`jti_hash`), expiry, revocation status, and metadata.
- Refresh flow rotates the session and revokes the previous session.
- Replay of old refresh tokens is rejected.
- Logout revokes all active refresh sessions for the user.

## 8. Credential and Secret Management

- `SECRET_KEY` and `DATABASE_KEY` are required in runtime configuration.
- Deployment tooling generates random keys when absent (`deploy.sh`).
- Secrets must not be committed to source control.

## 9. Access Provisioning and Deprovisioning

### 9.1 End-User Provisioning

- Users self-register through `POST /api/auth/register`.
- Duplicate usernames/emails are blocked.

### 9.2 End-User Deprovisioning

- Active session invalidation is supported via logout and refresh-session revocation.
- Full account/data deletion is currently an operator-run process documented in `docs/policies/DATA_RETENTION_AND_DELETION_SOP.md`.

## 10. Monitoring and Verification

- Security-focused automated tests validate key access controls:
  - Secure cookie settings and refresh rotation/replay protection (`backend/tests/test_auth_sessions.py`)
  - Secret-key fail-closed checks (`backend/tests/test_security_config.py`)
- Operational monitoring is currently based on application/container logs and health checks.

## 11. Current Limitations and Planned Maturity

The following are not currently implemented in this repository:

- App-native multi-factor authentication (MFA)
- Role-based admin model (application is single-role user model)
- Automated account lockout/rate limiting for login abuse
- Centralized audit log pipeline/SIEM

If Perkle is deployed directly on the public internet (without Tailscale access gating), app-native MFA should be implemented before production exposure. These items should be tracked in future security hardening work and reviewed during policy updates.

## 12. Policy Exceptions

Any exception to this policy requires explicit engineering approval and documentation of:

- Business justification
- Compensating controls
- Expiration date for the exception

## 13. Policy Review

- Review at least annually.
- Trigger immediate review after material changes to auth/session architecture, token handling, or access-sensitive API behavior.
