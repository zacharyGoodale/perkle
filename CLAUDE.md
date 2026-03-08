# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Perkle is a credit card benefit tracker. Users connect bank accounts via Plaid, and the system auto-detects used benefits via pattern matching on statement credits, or allows manual tracking. Benefits have different reset periods (monthly, quarterly, semi-annual, annual, cardmember year).

## Development Commands

### Backend (Python 3.12 + FastAPI)

```bash
cd backend
uv sync                                    # Install dependencies
uv run uvicorn app.main:app --reload       # Dev server on port 8000
uv run pytest                              # Run all tests
uv run pytest tests/test_benefit_detector.py  # Run single test file
uv run pytest -k "test_name"               # Run single test by name
```

Requires `SECRET_KEY` and `DATABASE_KEY` env vars (or `.env` file). Both must be cryptographically random, 32+ chars.

### Frontend (React 19 + Vite + TailwindCSS v4)

```bash
cd frontend
npm install                                # Install dependencies
npm run dev                                # Dev server on port 5173
npm run build                              # Production build (tsc + vite)
npm run lint                               # ESLint
```

Vite proxies `/api/*` to `http://localhost:8000` in dev.

### Production

```bash
./deploy.sh                                # Docker Compose + Tailscale serve on :8443
docker compose up -d --build               # Build and start containers
docker compose down                        # Stop
```

### Database Reset

Delete `backend/data/perkle.db` (dev) or `./data/perkle.db` (Docker) and restart backend.

## Architecture

### Backend

- **FastAPI app**: `backend/app/main.py` — mounts routers under `/api`, loads card configs on startup
- **API routes**: `backend/app/api/` — auth, benefits, cards, transactions, notifications
- **Auth deps**: `backend/app/api/deps.py` — JWT access tokens (15 min) + HttpOnly refresh cookies (7 days)
- **Database**: SQLAlchemy + SQLCipher (encrypted SQLite). Connection setup in `backend/app/database.py`
- **Config**: `backend/app/config.py` — pydantic-settings loaded from env vars, validates SECRET_KEY entropy
- **Card definitions**: YAML files in `backend/app/configs/cards/` — loaded into `card_configs` table on startup

### Key Data Flow

1. Card configs (YAML) load into DB on startup via `card_config_loader.py`
2. Users add cards to portfolio (`user_cards` table), optionally with `card_anniversary`
3. Plaid sync → `plaid_sync.py` → `transactions` table → `benefit_detector.py` matches credits to benefits
4. `benefit_periods` table tracks usage per benefit per period
5. Dashboard calls `/api/benefits/status` which calculates period boundaries and aggregates status

### Benefit Tracking Modes

- `auto`: Detected via statement credit patterns (e.g., "Platinum Resy Credit")
- `manual`: User marks as used (e.g., Uber Cash loaded to app)
- `info`: Informational only, no tracking (e.g., anniversary bonus miles)

### Benefit Reset Types

- `calendar_year`: Resets Jan 1 (or Jul 1 for semi-annual)
- `cardmember_year`: Resets on card anniversary date
- `rolling_years`: N years from last use (e.g., Global Entry every 4 years)

Period calculation logic: `backend/app/services/benefit_periods.py`

### Frontend

- **React Router**: `App.tsx` — public routes (Login, Register) and protected routes (Dashboard, Accounts, Cards, CardDetail)
- **Auth state**: `context/AuthContext.tsx` — tokens in React state, not localStorage
- **API client**: `lib/api.ts` — typed fetch wrapper with automatic token refresh
- **Styling**: TailwindCSS v4 via `@tailwindcss/vite` plugin
- **Data fetching**: TanStack React Query

Benefits display order: unused → partial → used → info (secondary sort by slug).

## Adding a New Card

1. Create YAML in `backend/app/configs/cards/<slug>.yaml`
2. Define: slug, name, issuer, annual_fee, benefits_url, account_patterns, benefits
3. Each benefit needs: slug, name, value, cadence, reset_type, tracking_mode
4. For auto-detection: add `detection_rules` with `credit_patterns` and `lookback_days`
5. Restart backend to reload configs

## Testing

Backend only (no frontend tests yet). Tests are in `backend/tests/` and use pytest with in-memory SQLite.

```bash
cd backend
uv run pytest                              # Run all tests
uv run pytest tests/test_benefit_detector.py  # Single file
uv run pytest -k "test_name"               # Single test by name
```

**Test setup pattern**: Each test file sets env vars at module level (`SECRET_KEY`, `DATABASE_KEY`, `DATABASE_URL`) via `os.environ.setdefault` before importing app modules. No shared conftest — each file is self-contained.

**API route tests** (e.g., `test_auth_sessions.py`): Create an in-memory SQLite engine, build a `FastAPI()` app with only the relevant router, and override `deps.get_db` with a test session factory. Use `TestClient` from FastAPI/Starlette.

**Service tests** (e.g., `test_benefit_detector.py`): Create an in-memory SQLite engine, set up models directly via SQLAlchemy session, call service functions, and assert on DB state.

**Config/security tests** (e.g., `test_security_config.py`, `test_sqlcipher_config.py`): Use `monkeypatch` to set env vars, reload modules via `importlib.import_module` (clearing `lru_cache` on `get_settings`), and assert that invalid configs raise exceptions.

Existing test files:
- `test_benefit_detector.py` — auto-detection idempotency
- `test_auth_sessions.py` — refresh cookie security, token rotation, replay prevention, logout
- `test_security_config.py` — SECRET_KEY validation (weak/missing/strong)
- `test_sqlcipher_config.py` — DATABASE_KEY validation, SQLCipher URL building

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy, SQLCipher (pysqlcipher3), Pydantic v2, uv
- **Frontend**: React 19, Vite 7, TailwindCSS v4, TypeScript 5.9, React Router 7, TanStack React Query, lucide-react
- **Deployment**: Docker Compose, nginx reverse proxy, Tailscale HTTPS on port 8443
