# Future Improvements

## Auth strategy (current state)

Perkle currently issues JWT access + refresh tokens from the backend and stores both in the browser
`localStorage` (`perkle_token` and `perkle_refresh`). The frontend attaches the access token to API
requests and refreshes on `401` when possible. This is simple and works well for a small deployment,
but it exposes tokens to JavaScript and therefore to any XSS vulnerability.

## Auth strategy (recommended alternatives)

Below are more secure approaches that reduce exposure of long-lived tokens in the browser.

### 1) HttpOnly refresh token cookie + in-memory access token (recommended next step)

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

### 2) HttpOnly cookies for both access + refresh

**How it works**
- Store both tokens in HttpOnly cookies.
- Backend auth middleware reads tokens from cookies instead of headers.

**Pros**
- Best XSS protection without server-side session state.
- Simplifies frontend token handling.

**Cons**
- Requires CSRF protection.
- More backend changes (cookie-based auth).

**Effort**
- Medium–high: larger backend changes and more testing effort.

### 3) Server-side sessions (opaque session ID cookie)

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

1. Agree on the target approach (option 1 is usually the best balance for a small app).
2. Add CSRF protections if moving to cookies.
3. Update auth endpoints to issue cookies and remove localStorage usage.
4. Update frontend to keep access tokens in memory only.
