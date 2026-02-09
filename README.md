# Perkle 🎯

A mobile-friendly web application for tracking credit card benefit usage. Never miss a perk again.

## Features

- **Automatic benefit detection** - Upload transaction CSVs and Perkle identifies when you've used card benefits
- **Multi-card support** - Track AMEX Gold, AMEX Platinum, Chase Sapphire Reserve, Capital One Venture X
- **Smart attribution** - Credits that post days after transactions are attributed to the correct period
- **Expiration alerts** - See what's expiring soon, get weekly email digests
- **Manual tracking** - Check off benefits that can't be auto-detected, with partial amount support
- **Benefit muting** - Hide benefits you don't use (Equinox, Saks, etc.)
- **Renewal reminders** - Know when your annual fee is coming up

## Quick Start

### Development

```bash
# Backend
cd backend
uv sync
uv run uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open your HTTPS Tailscale URL for authenticated testing (`https://<your-tailscale-hostname>:8443`).

Note: auth refresh sessions use `Secure` HttpOnly cookies and are intended for HTTPS browser access.

### Production (Docker + Tailscale)

```bash
./deploy.sh
```

Access at `https://<your-tailscale-hostname>:8443`

See [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) for full setup instructions.

## Documentation

- [Getting Started](docs/GETTING_STARTED.md) - Setup and deployment guide
- [Product Requirements](docs/PRD.md) - Features and user stories
- [Technical Design](docs/DESIGN.md) - Architecture and implementation details
- [Information Security Policy](docs/INFORMATION_SECURITY_POLICY.md) - Implemented security controls and risk procedures
- [Access Control Policy](docs/ACCESS_CONTROL_POLICY.md) - Authentication, authorization, and session control model
- [Privacy Policy](docs/PRIVACY_POLICY.md) - Private-use scope and data deletion contact
- [Data Retention & Deletion SOP](docs/DATA_RETENTION_AND_DELETION_SOP.md) - Retention policy and user deletion runbook

## Tech Stack

- **Backend**: Python 3.12 + FastAPI + SQLAlchemy + SQLCipher (SQLite)
- **Frontend**: React + Vite + TailwindCSS v4
- **Deployment**: Docker Compose + Tailscale

## Supported Cards (2026)

| Card | Annual Fee | Total Benefit Value |
|------|------------|--------------------|
| AMEX Gold | $325 | ~$424/year |
| AMEX Platinum | $895 | ~$2,800/year |
| Chase Sapphire Reserve | $795 | ~$1,800/year |
| Capital One Venture X | $395 | ~$520/year |

## Project Structure

```
perkle/
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── api/       # Route handlers
│   │   ├── configs/   # Card YAML definitions
│   │   ├── models/    # Database models
│   │   ├── schemas/   # Request/response schemas
│   │   └── services/  # Business logic
│   └── Dockerfile
├── frontend/          # React application
│   ├── src/
│   │   ├── pages/     # Dashboard, CardDetail, etc.
│   │   ├── lib/       # API client, utilities
│   │   └── context/   # Auth context
│   ├── nginx.conf     # Reverse proxy config
│   └── Dockerfile
├── docs/              # Documentation
├── deploy.sh          # Production deployment script
└── docker-compose.yml
```

## License

MIT
