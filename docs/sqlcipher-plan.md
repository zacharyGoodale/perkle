# SQLCipher Migration Plan (Docker on Linux)

## Goals
- Encrypt the SQLite database (`perkle.db`) at rest using SQLCipher.
- Preserve existing user data if feasible.
- Document operational steps for Docker-based deployments on Linux.
- Add testing steps to validate data integrity and encryption.

## Current State (Summary)
- Backend uses SQLite via SQLAlchemy with a file path `./data/perkle.db`.
- Docker Compose runs the stack and stores the DB on a mounted volume.

## Proposed Approach
Use SQLCipher to encrypt the SQLite database file at rest while keeping the existing schema and application logic intact. This requires:
- Installing SQLCipher libraries in the backend container.
- Switching the SQLAlchemy driver to a SQLCipher-compatible driver.
- Setting a database encryption key via environment variables.
- Migrating existing plaintext SQLite data to an encrypted SQLCipher database file.

## Implementation Plan

### 1) Dependencies & Driver
- Install SQLCipher in the backend Docker image.
  - For Debian/Ubuntu base images: install `sqlcipher` and `libsqlcipher-dev`.
  - For Alpine: install `sqlcipher` and `sqlcipher-dev`.
- Add a SQLCipher-capable driver (e.g., `pysqlcipher3`).
  - Update backend dependencies to include `pysqlcipher3` (or a supported SQLCipher SQLAlchemy dialect).

### 2) SQLAlchemy URL Updates
Update the database URL to use a SQLCipher-compatible scheme:
- Example: `sqlite+pysqlcipher:///./data/perkle.db`
- Add a new env var for the encryption key, e.g. `DATABASE_KEY`.
  - In Docker Compose, pass both `DATABASE_URL` (SQLCipher scheme) and `DATABASE_KEY`.

### 3) Key Management
- Store `DATABASE_KEY` as a Docker secret or env var in the deployment.
- Ensure the key is not committed to Git and is provided at runtime.
- Rotate keys by decrypting + re-encrypting the DB in a controlled maintenance window.

### 4) Database Initialization
- Modify DB initialization to apply the key on each connection:
  - For SQLCipher, execute `PRAGMA key = '...';` on connect.
  - Use SQLAlchemy event listeners to apply the key.

### 5) Migration Strategy (Preserve Data)
**Preferred (preserve data):**
1. Stop the backend service to avoid DB writes.
2. Backup plaintext DB:
   - `cp data/perkle.db data/perkle.db.bak`
3. Use `sqlcipher` tool to export plaintext and import encrypted:
   - Open plaintext DB with standard `sqlite3` to dump SQL.
   - Create new encrypted DB using `sqlcipher` and import the dump.
4. Replace `perkle.db` with encrypted version.
5. Start backend and run a quick sanity query.

**Alternative (drop data if migration too complex):**
- Stop backend.
- Remove `data/perkle.db`.
- Start backend to recreate schema.
- Notify users that data has been reset.

### 6) Docker Compose Updates (Linux)
- Add `DATABASE_KEY` to environment and switch `DATABASE_URL` to SQLCipher.
- Ensure volume mount path is unchanged so encrypted DB persists.
- Confirm container has access to SQLCipher libs.

### 7) Observability
- Add startup logs indicating DB encryption is enabled (do not log the key).
- Add health check to verify `SELECT count(*) FROM users` works after startup.

## Migration Steps (Detailed)

### A. One-time migration script (manual run)
1. Stop services:
   - `docker compose down`
2. Backup DB:
   - `cp data/perkle.db data/perkle.db.bak`
3. Export plaintext DB:
   - `sqlite3 data/perkle.db ".dump" > /tmp/perkle_plain.sql`
4. Create encrypted DB:
   - `sqlcipher data/perkle.db`
   - `PRAGMA key='${DATABASE_KEY}';`
   - `.read /tmp/perkle_plain.sql`
   - `PRAGMA cipher_integrity_check;`
   - `.exit`
5. Restart services:
   - `docker compose up -d --build`

### B. Sanity checks
- Connect to DB via SQLCipher and run:
  - `PRAGMA cipher_integrity_check;`
  - `SELECT count(*) FROM users;`

## Testing Plan
- **Unit/Integration:**
  - Run backend tests that touch the DB (e.g., benefit detector tests).
  - Validate migrations (alembic) still work.
- **Manual Verification:**
  - Authenticate via API and confirm normal operations.
  - Upload CSV and confirm transactions persist.
- **Negative Tests:**
  - Attempt to open DB via `sqlite3` without key; verify it fails or shows gibberish.

## Environment Considerations (Docker on Linux)
- Ensure the base image supports SQLCipher packages.
- Avoid storing keys in plaintext files within the repo.
- Use `.env` for local dev only; use Docker secrets or env injection for production.
- Ensure volume permissions allow the container user to read/write the encrypted DB file.

## Rollback Plan
- Stop services.
- Restore `perkle.db` from `.bak`.
- Revert DB URL and dependency changes.
- Restart services.

## Risks & Mitigations
- **Risk:** Migration failure corrupts DB.
  - **Mitigation:** Always back up first, validate integrity after migration.
- **Risk:** Key misconfiguration locks out app.
  - **Mitigation:** Validate key injection in staging before production.
- **Risk:** SQLCipher driver incompatibility.
  - **Mitigation:** Pin a supported SQLCipher-compatible driver and test in CI.
