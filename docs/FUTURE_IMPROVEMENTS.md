# Future Improvements

## Auth strategy (current state)

Perkle now uses:
- **Access tokens in memory only** (frontend runtime state)
- **Refresh tokens in Secure HttpOnly cookies**
- **Server-side refresh session rotation/revocation** (`refresh_sessions` table)

This removes long-lived token storage from browser JavaScript and enables real logout/session invalidation.

## Auth strategy (future alternatives)

### 1) HttpOnly cookies for both access + refresh

**How it works**
- Store refresh tokens in **HttpOnly, Secure** cookies.
- Keep access tokens in memory (React state) only.
- On expiration, call `/auth/refresh`, which reads the refresh cookie and issues new access tokens.

**Pros**
- Protects refresh tokens from XSS (not readable by JS).
- Minimal backend state changes (still JWT-based).

**Cons**
- Requires CSRF protections (same-site cookies or CSRF tokens).
- Requires some backend changes (cookie issuing, CORS settings).

**Effort**
- Medium: add cookie support in auth endpoints and update frontend to stop persisting refresh tokens.

### 2) Server-side sessions (opaque session ID cookie)

**How it works**
- Store sessions in the backend (DB or Redis).
- Client stores only a session ID cookie.

**Pros**
- Easy revocation and logout handling.
- No token theft risk from client storage.

**Cons**
- Requires server-side state and infrastructure.
- More complex scaling and deployment.

**Effort**
- High: new session store and middleware changes.

## Suggested next steps

1. Add explicit CSRF tokens for cookie-auth endpoints if cross-site flows are introduced.
2. Add session-management UI (view/revoke individual sessions/devices).
3. Add risk-based controls (rate limiting, suspicious login alerts).
