# Getting Started with Perkle

Perkle helps you track credit card benefits so you never miss a perk. This guide covers local development and production deployment.

## Prerequisites

- **Development**: Python 3.12+, Node.js 20+, uv (Python package manager)
- **Production**: Docker, Tailscale (optional, for remote access)

## Local Development

### Backend

```bash
cd backend

# Create virtual environment and install dependencies
uv sync

# Run the server
uv run uvicorn app.main:app --reload
```

Backend runs at http://localhost:8000

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

Frontend runs at http://localhost:5173

### First Steps

1. Open http://localhost:5173
2. Register an account
3. Add your credit cards (you'll be prompted for card anniversary date for CSR and Venture X)
4. Upload a transaction CSV from your financial aggregator
5. View your benefit status on the dashboard

## Production Deployment

### Quick Deploy (Linux server with Docker)

```bash
# Clone the repo
git clone <your-repo> perkle
cd perkle

# Deploy (creates .env, builds containers, configures Tailscale)
./deploy.sh
```

The script will:
1. Generate a secure `SECRET_KEY` in `.env`
2. Build and start Docker containers
3. Configure Tailscale to serve on port 8443

Access at `https://<your-tailscale-hostname>:8443`

### Manual Deploy

```bash
cd perkle

# Create environment file
echo "SECRET_KEY=$(openssl rand -hex 32)" > .env

# Build and run
docker compose up -d --build

# Configure Tailscale (optional)
tailscale serve --bg --https=8443 http://localhost:80
```

### Useful Commands

```bash
# View logs
docker compose logs -f

# Restart
docker compose restart

# Stop
docker compose down

# Rebuild after code changes
docker compose up -d --build
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key | `changeme-in-production` |
| `DATABASE_URL` | SQLite path | `sqlite:///data/perkle.db` |

### Adding Cards

Card configurations are in `backend/app/configs/cards/`. Each YAML file defines:
- Card metadata (name, issuer, annual fee)
- Benefits with detection rules
- Tracking mode (auto/manual/info)

See existing configs for examples.

## CSV Format

Perkle expects CSV exports with these columns:
- `date` - Transaction date
- `name` - Merchant/transaction description
- `amount` - Transaction amount (negative for credits)
- `account` - Card account name (used to match to your cards)

Compatible with Copilot Money and similar financial aggregators.

## Troubleshooting

### "Could not validate credentials"
Your account doesn't exist. Click "Create an account" to register.

### Benefits not auto-detecting
- Check that the credit transaction name matches patterns in the card config
- Verify the transaction date is within the lookback window
- Run benefit detection manually from the Upload page

### Database reset needed
Delete `backend/data/perkle.db` (or `./data/perkle.db` in Docker) and restart.
