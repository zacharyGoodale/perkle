# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Perkle is a credit card benefit tracker. Users upload transaction CSVs, and the system auto-detects used benefits (via pattern matching on statement credits) or allows manual tracking. Benefits have different reset periods (monthly, quarterly, semi-annual, annual, cardmember year).

## Development Commands

### Backend (FastAPI + SQLite)

```bash
cd backend
uv sync                                    # Install dependencies
uv run uvicorn app.main:app --reload       # Run dev server (port 8000)
```

### Frontend (React + Vite + TailwindCSS v4)

```bash
cd frontend
npm install                                # Install dependencies  
npm run dev                                # Run dev server (port 5173)
npm run build                              # Production build
npm run lint                               # ESLint
```

### Docker (Production)

```bash
docker compose up -d --build               # Build and start
docker compose logs -f                     # View logs
docker compose down                        # Stop
```

### Database Reset

Delete `backend/data/perkle.db` (dev) or `./data/perkle.db` (Docker) and restart the backend.

## Architecture

### Backend-Frontend Communication

- Frontend (nginx on port 80) proxies `/api/*` to backend (uvicorn on port 8000)
- In dev, frontend runs on 5173 and hits backend directly at 8000
- JWT auth: access tokens (15 min) + refresh tokens (7 days)

### Key Data Flow

1. **Card configs** are YAML files in `backend/app/configs/cards/` loaded into `card_configs` table on startup
2. **User adds cards** to their portfolio (`user_cards` table), optionally with `card_anniversary` for cardmember-year benefits
3. **CSV upload** → `csv_parser.py` → `transactions` table → `benefit_detector.py` matches credits to benefits
4. **Benefit periods** track usage per benefit per period in `benefit_periods` table
5. **Dashboard** calls `/api/benefits/status` which calculates current period boundaries and aggregates status

### Benefit Tracking Modes

- `auto`: Detected via statement credit patterns (e.g., "Platinum Resy Credit")
- `manual`: User marks as used (e.g., Uber Cash loaded to app)
- `info`: No tracking needed, just informational (e.g., anniversary bonus miles)

### Benefit Reset Types

- `calendar_year`: Resets Jan 1 (or Jul 1 for semi-annual)
- `cardmember_year`: Resets on card anniversary date
- `rolling_years`: N years from last use (e.g., Global Entry every 4 years)

Period calculation logic is in `backend/app/services/benefit_periods.py`.

### Frontend State

- Auth state in `AuthContext.tsx` (tokens stored in React state, not localStorage)
- API client in `lib/api.ts` with typed interfaces
- Benefits sorted: unused → partial → used → info (with secondary sort by slug for stability)

## Adding a New Card

1. Create YAML file in `backend/app/configs/cards/<slug>.yaml`
2. Define: slug, name, issuer, annual_fee, benefits_url, account_patterns, benefits
3. Each benefit needs: slug, name, value, cadence, reset_type, tracking_mode
4. For auto-detection: add `detection_rules` with `credit_patterns` and `lookback_days`
5. Restart backend to reload configs

## Key Files

- `backend/app/services/benefit_detector.py` - Auto-detection logic and status calculation
- `backend/app/services/benefit_periods.py` - Period boundary calculation
- `frontend/src/pages/Dashboard.tsx` - Main UI with benefit status display
- `frontend/src/pages/CardDetail.tsx` - Single card view with mark-as-used
- `frontend/src/lib/api.ts` - API client and TypeScript interfaces
