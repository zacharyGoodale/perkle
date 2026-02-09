# Technical Design: Perkle

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Tailscale                           │
│                    (https://*:8443)                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Docker Compose                         │
│  ┌─────────────────────┐    ┌─────────────────────────┐    │
│  │     Frontend        │    │       Backend           │    │
│  │   (nginx:80)        │───▶│   (uvicorn:8000)        │    │
│  │                     │    │                         │    │
│  │  React + Vite       │    │  FastAPI + SQLite       │    │
│  │  TailwindCSS v4     │    │                         │    │
│  └─────────────────────┘    └─────────────────────────┘    │
│                                       │                     │
│                                       ▼                     │
│                              ┌─────────────────┐           │
│                              │   ./data/       │           │
│                              │   perkle.db     │           │
│                              └─────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## Backend

### Stack
- **Python 3.12** with uv package manager
- **FastAPI** for REST API
- **SQLAlchemy** ORM with SQLite
- **Pydantic** for validation
- **PyJWT** for authentication

### Project Structure

```
backend/
├── app/
│   ├── api/                 # Route handlers
│   │   ├── auth.py         # Login, register, refresh
│   │   ├── cards.py        # Card portfolio management
│   │   ├── benefits.py     # Benefit status, mark used
│   │   ├── transactions.py # CSV upload
│   │   └── notifications.py# Email digest
│   ├── configs/cards/      # YAML card definitions
│   │   ├── amex-gold.yaml
│   │   ├── amex-platinum.yaml
│   │   ├── chase-sapphire-reserve.yaml
│   │   └── venture-x.yaml
│   ├── models/             # SQLAlchemy models
│   │   ├── user.py
│   │   ├── card.py
│   │   ├── transaction.py
│   │   └── benefit.py
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   │   ├── benefit_detector.py
│   │   ├── benefit_periods.py
│   │   ├── card_config_loader.py
│   │   ├── csv_parser.py
│   │   └── notifications.py
│   ├── config.py           # Settings from env
│   ├── database.py         # DB connection
│   └── main.py             # FastAPI app
├── Dockerfile
├── pyproject.toml
└── uv.lock
```

### Data Model

```
users
├── id (UUID)
├── username
├── email
├── password_hash
└── created_at

card_configs (seeded from YAML)
├── id (UUID)
├── slug
├── name
├── issuer
├── annual_fee
├── benefits_url
├── account_patterns (JSON)
└── benefits (JSON)

user_cards
├── id (UUID)
├── user_id → users
├── card_config_id → card_configs
├── nickname
├── card_anniversary (for cardmember_year benefits)
└── active

user_benefit_settings
├── id (UUID)
├── user_id → users
├── user_card_id → user_cards
├── benefit_slug
├── muted
└── notes

transactions
├── id (UUID)
├── user_id → users
├── external_id (dedup key)
├── date
├── merchant
├── amount
├── account
├── card_config_id → card_configs
└── raw_data (JSON)

benefit_periods
├── id (UUID)
├── user_card_id → user_cards
├── benefit_slug
├── period_start
├── period_end
├── amount_limit
├── amount_used
├── usage_count
├── completed
└── completed_at
```

### Key APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Create account |
| `/api/auth/login` | POST | Get JWT tokens |
| `/api/cards/available` | GET | List card configs |
| `/api/cards/my` | GET/POST/DELETE | User's card portfolio |
| `/api/benefits/status` | GET | All benefit statuses |
| `/api/benefits/mark-used` | POST | Manual tracking |
| `/api/transactions/upload` | POST | CSV import |
| `/api/notifications/digest/send` | POST | Trigger email |

### Benefit Period Calculation

Benefits reset at different times:
- **calendar_year**: Jan 1 / Jul 1 for semi-annual
- **cardmember_year**: Based on card anniversary date
- **rolling_years**: N years from last use (e.g., Global Entry every 4 years)

```python
def get_period_boundaries(cadence, reference_date, card_anniversary, reset_type):
    if reset_type == "cardmember_year" and card_anniversary:
        # Calculate period based on anniversary
        ...
    elif cadence == "monthly":
        # First to last day of month
        ...
    elif cadence == "semi-annual":
        # Jan-Jun or Jul-Dec
        ...
```

## Frontend

### Stack
- **React 18** with TypeScript
- **Vite** for bundling
- **TailwindCSS v4** for styling
- **React Router** for navigation
- **Lucide React** for icons

### Project Structure

```
frontend/
├── src/
│   ├── components/         # Reusable UI components
│   ├── context/
│   │   └── AuthContext.tsx # JWT token management
│   ├── lib/
│   │   ├── api.ts         # API client + types
│   │   └── utils.ts       # cn() helper
│   ├── pages/
│   │   ├── Dashboard.tsx  # Home view
│   │   ├── CardDetail.tsx # Single card benefits
│   │   ├── Cards.tsx      # Portfolio management
│   │   ├── Upload.tsx     # CSV import
│   │   ├── Login.tsx
│   │   └── Register.tsx
│   ├── App.tsx            # Router setup
│   └── main.tsx
├── Dockerfile
├── nginx.conf             # Reverse proxy config
├── package.json
└── vite.config.ts
```

### Key Features

**Dashboard**
- Summary card with total used/available
- Aggregate "Unused Benefits" sorted by days remaining
- Per-card benefit preview (sorted: unused → partial → used → info)
- Renewal warnings banner

**Card Detail**
- Full benefit list with progress bars
- Mark as used with partial amount input
- Mute/unmute toggle
- Link to official benefits page
- Days until renewal

**Benefit Sorting**
```typescript
const sortedBenefits = benefits.sort((a, b) => {
  const statusOrder = (status, trackingMode) => {
    if (trackingMode === 'info') return 4;
    if (status === 'used') return 3;
    if (status === 'partial') return 2;
    return 1; // available, expiring
  };
  const diff = statusOrder(a.status, a.tracking_mode) - statusOrder(b.status, b.tracking_mode);
  return diff !== 0 ? diff : a.slug.localeCompare(b.slug);
});
```

## Deployment

### Docker Compose

```yaml
services:
  backend:
    build: ./backend
    volumes:
      - ./data:/app/data
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=sqlite+pysqlcipher:///data/perkle.db
      - DATABASE_KEY=${DATABASE_KEY}

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;

    # API proxy to backend container
    location /api {
        proxy_pass http://backend:8000/api;
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### Tailscale Integration

Exposes the app securely on your Tailscale network:

```bash
tailscale serve --bg --https=8443 http://localhost:80
```

Access at `https://<hostname>:8443` from any device on your tailnet.

## Security

- Passwords hashed with bcrypt
- JWT access tokens (15 min) + refresh tokens (7 days)
- CORS restricted to localhost origins in dev
- Tailscale provides network-level security in prod
- No sensitive data in client-side storage (tokens in memory/context)

## Future Enhancements

- Plaid integration for automatic transaction import
- Push notifications via web push API
- Multiple CSV format support (Mint, Monarch, etc.)
- Household/shared accounts
- Points/miles tracking
