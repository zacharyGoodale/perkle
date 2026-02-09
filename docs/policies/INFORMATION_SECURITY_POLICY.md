# Perkle Information Security Policy

## 1. Document Control

- Owner: Perkle engineering
- Version: 1.0
- Effective date: 2026-02-09
- Review cadence: At least annually and after material architecture/authentication changes

## 2. Purpose

This policy defines how Perkle identifies, mitigates, and monitors information security risks for the current application architecture.

Perkle is a web application that stores user account data, card portfolio metadata, uploaded transaction records, benefit usage state, and refresh-session metadata. The backend is FastAPI + SQLAlchemy + SQLite/SQLCipher; the frontend is React/Vite behind nginx.

## 3. Scope

This policy applies to:

- Backend API and data layer (`backend/app/*`)
- Frontend authentication and API client logic (`frontend/src/context/AuthContext.tsx`, `frontend/src/lib/api.ts`)
- Container/deployment configuration (`docker-compose.yml`, `deploy.sh`, `backend/Dockerfile`)
- Production database files mounted under `./data`

## 4. Security Control Baseline (Implemented)

### 4.1 Authentication and Session Management

- Passwords are stored as bcrypt hashes (`backend/app/api/auth.py`).
- Access tokens are short-lived JWTs (default 15 minutes) with explicit token type `access` (`backend/app/api/auth.py`, `backend/app/config.py`).
- Refresh tokens are issued as `HttpOnly`, `Secure`, `SameSite=Lax` cookies scoped to `/api/auth` (`backend/app/api/auth.py`, `backend/app/config.py`).
- Refresh sessions are persisted server-side and rotated on each refresh; replayed refresh tokens are rejected (`backend/app/api/auth.py`, `backend/app/models/auth.py`).
- Logout revokes all active refresh sessions for the user (`backend/app/api/auth.py`).
- Frontend stores access tokens in memory (not localStorage) and refreshes through cookie-based flow (`frontend/src/context/AuthContext.tsx`, `frontend/src/lib/api.ts`).

### 4.2 Secrets and Key Management

- `SECRET_KEY` and `DATABASE_KEY` are required at startup (`backend/app/config.py`, `backend/app/database.py`, `docker-compose.yml`).
- `SECRET_KEY` is validated for minimum length and estimated entropy; weak placeholder values fail closed (`backend/app/config.py`).
- Deployment script generates strong random secrets when missing (`deploy.sh`).

### 4.3 Data Encryption

- Database-at-rest encryption is supported with SQLCipher (`sqlite+pysqlcipher`) (`backend/app/database.py`, `backend/Dockerfile`).
- SQLCipher key material is passed via environment variable and injected into the connection URL when needed (`backend/app/database.py`).
- SQLCipher memory security pragma is enabled on database connect (`backend/app/database.py`).

### 4.4 Authorization and API Protection

- Protected endpoints require bearer access tokens via dependency checks (`backend/app/api/deps.py` and authenticated API routes).
- CORS is explicitly configured to known development origins (`backend/app/main.py`).

### 4.5 Data Minimization in Auth Responses

- Login returns access token only; refresh token is not returned in JSON and is only set as cookie (`backend/app/api/auth.py`).

### 4.6 Security Verification Tests

- Tests validate secret-key fail-closed behavior (`backend/tests/test_security_config.py`).
- Tests validate SQLCipher key requirements and import fail-closed behavior (`backend/tests/test_sqlcipher_config.py`).
- Tests validate secure cookie flags, refresh rotation/replay prevention, and logout revocation (`backend/tests/test_auth_sessions.py`).

## 5. Risk Management Procedure (Operationalized)

### 5.1 Identify Risks

At minimum on each release that changes auth, data storage, or deployment:

1. Review changed files for security impact (`backend/app/api/auth.py`, `backend/app/database.py`, `backend/app/config.py`, deployment configs).
2. Identify risks in these categories:
   - Authentication/session abuse
   - Secret/key exposure
   - Unauthorized data access
   - Data-at-rest exposure
   - Data deletion/retention handling gaps

### 5.2 Mitigate Risks

For identified risks, apply one or more of:

- Code changes in backend/frontend
- Config hardening (`.env`, Docker env, cookie flags)
- Schema/model updates for session/data controls
- Test additions for new security behavior
- Documentation/runbook updates in `docs/`

### 5.3 Monitor Controls

Current monitoring is operational and lightweight:

- Container health checks for backend availability (`docker-compose.yml`)
- API/runtime logs and manual review during incidents
- Periodic verification by running security-focused tests in `backend/tests/`

Note: Centralized security telemetry/SIEM and automated intrusion detection are not currently implemented in this repository.

## 6. Access and Change Governance

- Production secrets must be environment-managed and never committed.
- Security-sensitive code changes require review before deployment.
- Any change to token lifetimes, cookie security flags, or encryption settings requires corresponding test updates and document review.

## 7. Incident Handling (Current Process)

If unauthorized access, session abuse, or key exposure is suspected:

1. Contain:
   - Rotate `SECRET_KEY` and/or `DATABASE_KEY` as applicable.
   - Revoke active refresh sessions (global logout support exists at user level in app logic).
2. Eradicate:
   - Patch vulnerable code path and redeploy.
3. Recover:
   - Validate health checks and authentication flows.
4. Document:
   - Record timeline, root cause, and corrective actions in internal engineering notes.

## 8. Policy Review

- This policy is reviewed at least annually.
- Immediate review is required after significant auth or encryption changes (for example, token architecture changes, key handling changes, or DB encryption changes).
