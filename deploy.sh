#!/bin/bash
# Install and run Perkle with Docker + Tailscale

set -e

echo "Installing Perkle..."
echo ""

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# Check for docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed."
    exit 1
fi

# Create data directory
mkdir -p "$PROJECT_DIR/data"

# Create .env if it doesn't exist
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "Creating .env file..."
    echo "SECRET_KEY=$(openssl rand -hex 32)" > "$PROJECT_DIR/.env"
    echo "✓ Created .env with secure secret key"
fi

# Build and start containers
echo "Building and starting Docker containers..."
docker-compose up -d --build
echo "✓ Containers started"

# Configure Tailscale serve (using port 8443 to avoid conflict with amuse-bouche on 443)
if command -v tailscale >/dev/null 2>&1; then
    echo ""
    echo "Configuring Tailscale serve on port 8443..."
    if tailscale serve --bg --https=8443 http://localhost:80 2>&1; then
        HOSTNAME=$(tailscale status --json 2>/dev/null | jq -r '.Self.DNSName' 2>/dev/null | sed 's/\.$//' || echo "<your-machine>")
        echo "✓ Tailscale serve enabled"
    else
        echo "⚠️  Tailscale serve configuration failed"
        echo "   You can manually configure with: tailscale serve --bg --https=8443 http://localhost:80"
        HOSTNAME="<your-machine>"
    fi
else
    echo "⚠️  Tailscale not found - skipping Tailscale configuration"
    HOSTNAME="<your-machine>"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✓ Perkle is now running!"
echo ""
echo "Docker handles:"
echo "  • Auto-restart on crash"
echo "  • Auto-start on boot (via Docker daemon)"
echo ""
echo "Useful commands:"
echo "  • View logs:     docker-compose logs -f"
echo "  • Stop:          docker-compose down"
echo "  • Restart:       docker-compose restart"
echo "  • Rebuild:       docker-compose up -d --build"
echo ""
echo "Local access:     http://localhost"
echo "Tailscale access: https://${HOSTNAME}:8443"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
