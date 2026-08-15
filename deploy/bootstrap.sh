#!/bin/bash
# SAHIIX Production Bootstrap
# Run on fresh Ubuntu 22.04+ VPS as root

set -euo pipefail

REPO_DIR="/opt/sahiix"
REPO_URL="https://github.com/sahiixx/agentic-harness-integration"

log() { echo "[$(date '+%H:%M:%S')] $*"; }

# ─── Pre-flight ───
log "Checking system..."
[[ $EUID -eq 0 ]] || { log "Run as root"; exit 1; }
command -v docker >/dev/null || { log "Installing Docker..."; curl -fsSL https://get.docker.com | sh; }
command -v docker-compose >/dev/null || { log "Installing Docker Compose..."; apt-get update && apt-get install -y docker-compose-plugin; }

# ─── Clone Repo ───
log "Cloning repository..."
mkdir -p "$REPO_DIR"
cd "$REPO_DIR"
[[ -d .git ]] || git clone "$REPO_URL" .

# ─── Environment ───
log "Checking environment..."
[[ -f .env.production ]] || { log "Creating .env.production from template..."; cp deploy/.env.production.template .env.production; log "EDIT .env.production WITH ALL SECRETS BEFORE CONTINUING"; exit 1; }

# ─── Systemd Services ───
log "Installing systemd services..."
cp deploy/systemd/*.service /etc/systemd/system/
systemctl daemon-reload

# ─── Docker Networks/Volumes ───
log "Creating Docker networks..."
docker network create sahiix-internal 2>/dev/null || true
docker network create sahiix-external 2>/dev/null || true

# ─── Pull/Build Images ───
log "Building Docker images..."
docker-compose -f deploy/docker-compose.prod.yml build --parallel

# ─── Start Core Services ───
log "Starting core infrastructure..."
docker-compose -f deploy/docker-compose.prod.yml up -d postgres redis
sleep 10

# ─── Database Init ───
log "Initializing database..."
docker-compose -f deploy/docker-compose.prod.yml exec -T postgres psql -U sahiix -d sahiix -f /scripts/init-db.sql

# ─── Start All Services ───
log "Starting all services..."
docker-compose -f deploy/docker-compose.prod.yml up -d

# ─── Nginx Certbot ───
log "Waiting for services..."
sleep 15

# ─── Health Checks ───
log "Running health checks..."
for i in {1..30}; do
    if curl -sf http://localhost:8000/health >/dev/null && curl -sf http://localhost:3000 >/dev/null; then
        log "✅ Core services healthy"
        break
    fi
    sleep 2
done

# ─── SSL Certificate ───
log "Requesting SSL certificate..."
docker-compose -f deploy/docker-compose.prod.yml run --rm certbot certonly --webroot -w /var/www/certbot -d "${DOMAIN}" --email "admin@${DOMAIN}" --agree-tos --no-effort --force-renewal 2>/dev/null || log "Certbot failed (check DNS/domain)"

# ─── Reload Nginx ───
docker-compose -f deploy/docker-compose.prod.yml exec nginx nginx -s reload 2>/dev/null || true

# ─── Enable Systemd Services ───
log "Enabling systemd services..."
systemctl enable sahiix-api sahiix-web sahiix-hermes sahiix-unified sahiix-ollama 2>/dev/null || true

log "🎉 DEPLOYMENT COMPLETE"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "API:       https://${DOMAIN}/api/harness"
log "Web:       https://${DOMAIN}"
log "Grafana:   https://${DOMAIN}/grafana"
log "Health:    https://${DOMAIN}/api/harness/health"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Next steps:"
log "  1. Verify all endpoints return 200"
log "  2. Configure Grafana alerts"
log "  3. Test Telegram /status"
log "  4. Verify daily backups in S3"