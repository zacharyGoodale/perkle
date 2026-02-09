# SQLCipher Migration Plan (Docker on Linux)

## Goals
- Encrypt `data/perkle.db` at rest with SQLCipher.
- Preserve all existing application data.
- Keep rollback straightforward.

## Current Runtime Assumptions
- Docker volume mount is `./data:/app/data`.
- Backend DB URL is `sqlite+pysqlcipher:///data/perkle.db`.
- Encryption key is provided with `DATABASE_KEY`.
- `DATABASE_KEY` is required at startup.

## Recommended Migration Method
Use SQLCipher's `ATTACH ... KEY` + `sqlcipher_export(...)` flow. This avoids fragile dump/reimport edge cases and preserves schema, indexes, and data in one step.

## One-Time Migration Procedure
Use `docker compose` if available, otherwise `docker-compose`.

1. Stop writes:
   - `docker compose down`
2. Backup plaintext DB:
   - `cp data/perkle.db data/perkle.db.bak.$(date +%Y%m%d-%H%M%S)`
3. Export plaintext into encrypted DB:
   - Run inside backend image so SQLCipher tooling is guaranteed:
```bash
docker compose run --rm backend sh -lc '
set -euo pipefail
test -n "$DATABASE_KEY"
rm -f /app/data/perkle.encrypted.db
sqlcipher /app/data/perkle.db <<SQL
ATTACH DATABASE "/app/data/perkle.encrypted.db" AS encrypted KEY "$DATABASE_KEY";
SELECT sqlcipher_export('"'"'encrypted'"'"');
DETACH DATABASE encrypted;
.exit
SQL
'
```
4. Validate encrypted DB:
```bash
docker compose run --rm backend sh -lc '
set -euo pipefail
sqlcipher /app/data/perkle.encrypted.db <<SQL
PRAGMA key = "$DATABASE_KEY";
PRAGMA cipher_integrity_check;
SELECT count(*) FROM users;
SELECT count(*) FROM transactions;
SELECT count(*) FROM benefit_periods;
.exit
SQL
'
```
5. Cut over:
   - `mv data/perkle.db data/perkle.db.precutover.$(date +%Y%m%d-%H%M%S)`
   - `mv data/perkle.encrypted.db data/perkle.db`
6. Restart:
   - `docker compose up -d --build`

## Post-Migration Verification
- Backend container starts without SQLCipher errors.
- Healthcheck passes.
- App login and dashboard load successfully.
- Negative check:
  - opening `data/perkle.db` without a key fails with `file is not a database`.

## Rollback
1. Stop services:
   - `docker compose down`
2. Restore backup:
   - `cp data/perkle.db.bak.<timestamp> data/perkle.db`
3. Start services:
   - `docker compose up -d`

## Operational Notes
- Never commit `DATABASE_KEY`.
- Keep at least one timestamped backup until you validate production traffic.
- For key rotation, run the same export flow into a new DB with a new key during a maintenance window.
