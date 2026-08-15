# SAHIIX Production Deployment

## Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/sahiixx/agentic-harness-integration
cd agentic-harness-integration

# 2. Copy and fill env template
cp deploy/.env.production.template .env.production
# Edit .env.production with all secrets

# 3. Deploy
./deploy/bootstrap.sh
```

## Services (20 containers)

| Service | Port | Purpose |
|---------|------|---------|
| nginx | 80/443 | Reverse proxy + TLS |
| api | 8000 | FastAPI v6 (Grok, Swarm, Dashboard) |
| web | 3000 | Next.js 16.3 console |
| hermes | 8765/8766 | SAHIIX OS (Telegram, MCP, WA) |
| unified-system | - | Orchestrator + health/self-heal |
| ollama | 11434 | Local LLMs (nemotron-3-super, etc.) |
| postgres | 5432 | pgvector + app data |
| redis | 6379 | Cache + rate limits |
| prometheus | 9090 | Metrics |
| grafana | 3001 | Dashboards |
| loki | 3100 | Logs |
| promtail | - | Log shipper |
| certbot | - | Let's Encrypt TLS |
| backup | - | Daily PG + config → S3 |

## Key Features

- **Multi-model Swarm**: Parallel Ollama + FreeTheAI + Puter
- **Grok 4.6 Native**: xAI SDK with tools (web_search, code_exec)
- **Free Provider Fallback**: Ollama → FreeTheAI → Puter → stub
- **14-Repo Upgrade Registry**: 3 tiers, auto-updated
- **5hr Autonomous Grok**: Self-improvement loop
- **Unified Orchestrator**: Health checks, self-heal, Telegram alerts
- **Production Observability**: Prometheus + Grafana + Loki
- **Automated TLS**: Let's Encrypt via certbot
- **Daily Backups**: PG dump + configs → S3

## Required Secrets (`.env.production`)

```bash
POSTGRES_PASSWORD=...
JWT_SECRET=...
XAI_API_KEY=...           # x.ai/api
FREETHEAI_API_KEY=...     # Discord /signup
PUTER_AUTH_TOKEN=...      # puter.com
TELEGRAM_BOT_TOKEN=...    # @BotFather
TELEGRAM_CHAT_ID=...      # @userinfobot
TELEGRAM_ADMIN_USERNAME=...
GRAFANA_ADMIN_PASSWORD=...
DOMAIN=yourdomain.com
S3_ENDPOINT=...           # Optional
S3_BUCKET=...             # Optional
S3_ACCESS_KEY=...         # Optional
S3_SECRET_KEY=...         # Optional
```

## Deploy

```bash
# On fresh VPS (Ubuntu 22.04+)
curl -fsSL https://raw.githubusercontent.com/sahiixx/agentic-harness-integration/main/deploy/bootstrap.sh | bash
```

## Architecture

```
                    ┌─────────────────┐
                    │    Internet     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    nginx:443    │  (TLS, rate limit, WAF)
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
   ┌──────────┐        ┌──────────┐        ┌──────────┐
   │   web    │        │   api    │        │ grafana  │
   │  :3000   │        │  :8000   │        │  :3001   │
   └──────────┘        └────┬─────┘        └──────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐   ┌──────────┐
        │postgres  │  │  redis   │   │ ollama   │
        │ pgvector │  │  cache   │   │  LLMs    │
        └──────────┘  └──────────┘   └──────────┘
              │              │              │
              ▼              ▼              ▼
        ┌──────────────────────────────────────────┐
        │         Observability Stack              │
        │  Prometheus ← Loki ← Promtail ← Grafana  │
        └──────────────────────────────────────────┘
```

## Production Checklist

- [ ] VPS provisioned (2+ CPU, 4GB+ RAM, 50GB+ SSD)
- [ ] Domain DNS → VPS IP
- [ ] All secrets in `.env.production`
- [ ] `./deploy/bootstrap.sh` completes
- [ ] Grafana dashboards visible at `https://domain/grafana`
- [ ] API health at `https://domain/api/harness/health`
- [ ] Web console at `https://domain`
- [ ] Telegram `/status` works
- [ ] Daily backup verified in S3
- [ ] Alert rules configured in Prometheus