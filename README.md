# Agentic Harness Integration Layer v6

Production bridge wiring [sahiixx/agentic-harness](https://github.com/sahiixx/agentic-harness) patterns to the full stack.

## What v6 Fixes

| Issue | v5 State | v6 Fix |
|---|---|---|
| GapClaw test failure | Test supplied 3 mocks, code needed 5 → `StopAsyncIteration` | Test now supplies correct 5-call mock sequence |
| Subtask parser empty input | `_parse_subtasks("")` returned `[]`, test expected `[""]` | Added `if not raw.strip(): return [""]` guard |
| Tool async/sync mismatch | Tests used `AsyncMock` for response objects → `json()` returned coroutine | Tests now use `Mock` (sync) for response, `AsyncMock` only for client |
| Test count accuracy | README claimed 30 tests, actual was 31 collected | README reports actual count |
| Mock propagation | Bridges used `from api.core import azure_complete` | All now use `import api.core as core` — single patch propagates |
| SSE streaming | No dedicated test | `GET /stream/trace/{trace_id}` endpoint + test |
| n8n node | Stub only | Full community node with credentials, 11 operations |
| React frontend | Standalone scaffold | Next.js 14 app router with Pattern Tester + SSE demo |
| Live validation | No smoke test | `tests/test_live_smoke.py` — skipped without real keys |

## Architecture

```
core.py          ← models, azure_complete, azure_embed, now, Trace
  ↑
bridges/         ← nexus, gapclaw, sara, gapsolver (import core)
  ↑
main.py          ← FastAPI app (import core + bridges)
  ↑
tests/           ← patch core.azure_complete, conftest.py blocks real network
```

## Stack Map

| Layer | Tech | File |
|---|---|---|
| Core (shared) | Pydantic + httpx | `api/core.py` |
| API | FastAPI | `api/main.py` |
| Database | asyncpg + PostgreSQL | `api/db.py` |
| Cache | redis-py + Redis | `api/redis_client.py` |
| Tools | Apollo, Bright Data, WATI | `api/tools/` |
| NEXUS | 4-worker orchestration | `api/nexus_bridge.py` |
| GapClaw | ReAct + real tools + budget | `api/gapclaw_bridge.py` |
| SARA | Eval-Optimize + Reflect | `api/sara_bridge.py` |
| GapSolver | Gap discovery | `api/gapsolver_bridge.py` |
| Frontend | Next.js 14 + App Router | `web/` |
| Automation | n8n community node | `n8n/` |
| Infra | Docker Compose (prod + dev) | `docker-compose.yml`, `docker-compose.dev.yml` |
| CI | GitHub Actions | `.github/workflows/harness-self-test.yml` |

## Quick Deploy

```bash
# Production
cp .env.example .env
docker-compose up --build

# Development (hot reload, exposed DB/Redis)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

## API Endpoints

### Base Patterns

| Endpoint | Pattern |
|---|---|
| `POST /pattern/chain` | Prompt Chaining |
| `POST /pattern/route` | Routing |
| `POST /pattern/parallel` | Parallelization |
| `POST /pattern/orchestrate` | Orchestrator-Workers (optional GapSolver pre-analysis) |
| `POST /pattern/evaluate_optimize` | Evaluator-Optimizer |
| `POST /pattern/react` | ReAct |
| `POST /pattern/reflect` | Reflection |

### Domain Bridges

| Endpoint | Description |
|---|---|
| `POST /nexus/enrich` | 4-worker lead enrichment |
| `POST /gapclaw/hunt` | Autonomous ReAct with real business discovery |
| `POST /sara/generate` | Rubric-gated video script generation |
| `POST /gapsolver/discover` | Revenue-scored gap discovery |

### Streaming

| Endpoint | Description |
|---|---|
| `GET /stream/trace/{trace_id}` | SSE stream for real-time trace updates |

### Observability

| Endpoint | Description |
|---|---|
| `GET /health` | Service health |
| `GET /traces/escalated` | Human review queue |

## Environment Variables

| Variable | Purpose |
|---|---|
| `AZURE_FOUNDRY_API_KEY` | Azure AI Foundry |
| `AZURE_FOUNDRY_BASE_URL` | Azure endpoint |
| `AZURE_DEFAULT_MODEL` | General reasoning (default: gpt-5.6-sol) |
| `AZURE_JUDGE_MODEL` | Deep evaluation (default: claude-opus-5) |
| `DATABASE_URL` | PostgreSQL connection |
| `REDIS_URL` | Redis connection |
| `APOLLO_API_KEY` | B2B lead discovery |
| `BRIGHTDATA_API_KEY` | Web scraping / SERP |
| `WATI_API_KEY` | WhatsApp Business API |

## Verification

```bash
cd api
pytest ../tests/ -v --ignore=../tests/test_live_smoke.py
```

### Test Suite

| Suite | Tests | What They Cover |
|---|---|---|
| `test_patterns.py` | 19 | 7 patterns + SSE + subtask parser (4 cases) + API endpoints + health + safety net |
| `test_bridges.py` | 4 | NEXUS, GapClaw (budget-verified), SARA, GapSolver |
| `test_tools.py` | 9 | Apollo, Bright Data, WATI, retry logic, failure handling, cost tracking |
| `test_live_smoke.py` | 4 | Live Azure complete, embed, health, GapClaw (skipped without keys) |
| **Total (mocked)** | **32** | **All mocked — no real network calls** |
| **Total (with live)** | **36** | **Includes 4 live smoke tests** |

### Safety Net

`tests/conftest.py` auto-patches `httpx.AsyncClient.post/get/request` to raise `RuntimeError("REAL NETWORK CALL BLOCKED")` if any test forgets to mock a network call.

### Mocking Strategy

All modules use `import api.core as core` + `core.azure_complete()`. Tests patch `api.core.azure_complete` once and it propagates everywhere.

Tool tests use `Mock` (sync) for `httpx.Response` objects and `AsyncMock` only for `AsyncClient` methods, matching httpx's actual API where `Response.json()` is synchronous.

## CI/CD Pipeline

1. Circular import check
2. Full mocked test suite — 32 tests, zero real network calls
3. Safety net verification
4. Docker Compose validation
5. Live smoke test (main branch only, requires real Azure keys in secrets)

## Honest Status

| Aspect | State |
|---|---|
| Architecture | ✅ Circular-import-free, mockable |
| Tests (mocked) | ✅ 32 tests, zero real network calls |
| Test safety net | ✅ `RuntimeError` on unmocked HTTP |
| Tool HTTP abstraction | ✅ `.post()`/`.get()` direct, sync response handling |
| GapClaw determinism | ✅ `max_model_calls` budget |
| Orchestrator JSON | ✅ `_parse_subtasks()` handles all shapes |
| Mutable defaults | ✅ `Field(default_factory=list)` |
| Azure client | ✅ Key guard, proper Claude payload, random jitter |
| Docker production | ✅ Non-root, workers, healthchecks, resource limits |
| Database/Redis | ✅ Graceful degradation |
| Docker Compose validation | ✅ CI checks `docker-compose config` |
| SSE streaming | ✅ Endpoint + dedicated test |
| n8n node | ✅ Full community node with credentials, 11 operations |
| React frontend | ✅ Next.js 14 app router with Pattern Tester + SSE demo |
| Live Azure validation | ✅ `test_live_smoke.py` — skipped without keys |

## Changelog

- **v6**: Fixed GapClaw test mock sequence, subtask parser empty input, tool test async/sync mismatch, mock propagation via `import api.core as core`, SSE endpoint + test, n8n community node, Next.js 14 frontend, live smoke tests.
- **v5**: Fixed tool HTTP abstraction, GapClaw budget, orchestrator JSON validation, mutable defaults, Azure hardening, Docker production config.
- **v4**: Fixed testability — all modules use `import core`.
- **v3**: Fixed circular imports by extracting `core.py`.
- **v2**: Initial integration layer with real tool clients and PostgreSQL/Redis.
