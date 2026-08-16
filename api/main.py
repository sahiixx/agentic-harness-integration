"""Agentic Harness Integration Layer — FastAPI application."""
from __future__ import annotations

import asyncio
import json
import os
from typing import Any

# Disable uvloop on Android/Termux (libuv assertion failure)
try:
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
except Exception:
    pass

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, status, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

import api.core as core
from api.auth import verify_token, rate_limit_middleware, create_token
from api.nexus_bridge import enrich_lead
from api.gapclaw_bridge import hunt
from api.sara_bridge import generate_script
from api.gapsolver_bridge import discover_gaps
from api.grok_bridge import grok_chat, grok_vision, grok_voice_transcribe, grok_voice_speak, grok_chat_free, grok_vision_free, FREE_PROVIDERS
from api.azure_openai_bridge import azure_chat, azure_embeddings, azure_chat_stream
from api.swarm import swarm_chat
from api.repo_registry import list_repos, summary as repo_summary

# Production hardening
from api.production import (
    RequestIDMiddleware,
    RedisRateLimiter,
    CircuitBreaker,
    health_registry,
    ErrorResponse,
    config,
    get_request_id,
)

app = FastAPI(
    title="Agentic Harness Bridge",
    version="6.0.0",
    description="Agentic Harness Bridge v6",
)

# Rate limiting middleware
app.middleware("http")(rate_limit_middleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID tracing
app.add_middleware(RequestIDMiddleware)

# Redis rate limiter
rate_limiter = RedisRateLimiter(os.getenv("REDIS_URL", "redis://localhost:6379"))

# Prometheus metrics
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


# ---------------------------------------------------------------------------
# Auth helper — disabled when JWT_SECRET is not set
# ---------------------------------------------------------------------------

async def _auth(payload: dict = Depends(verify_token)) -> dict:
    return payload


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------

class ChainRequest(BaseModel):
    prompts: list[str] = Field(default_factory=list)
    temperature: float = 0.7


class RouteRequest(BaseModel):
    input_text: str = ""
    routes: dict[str, str] = Field(default_factory=dict)


class ParallelRequest(BaseModel):
    tasks: list[str] = Field(default_factory=list)
    temperature: float = 0.7


class OrchestrateRequest(BaseModel):
    objective: str = ""
    pre_analyze: bool = False


class EvalOptimizeRequest(BaseModel):
    prompt: str = ""
    rubric: dict[str, Any] = Field(default_factory=dict)
    max_iterations: int = 3


class ReActRequest(BaseModel):
    query: str = ""
    max_model_calls: int = 8


class ReflectRequest(BaseModel):
    draft: str = ""
    criteria: list[str] = Field(default_factory=list)


class NexusEnrichRequest(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    company: str = ""
    title: str = ""
    linkedin: str = ""


class SaraGenerateRequest(BaseModel):
    topic: str = ""
    rubric: dict[str, Any] = Field(default_factory=dict)
    max_iterations: int = 3


class GapSolverDiscoverRequest(BaseModel):
    industry: str = ""
    location: str = "Dubai"
    top_n: int = 5


class TokenRequest(BaseModel):
    subject: str = ""
    expires_minutes: int = 60


# ---------------------------------------------------------------------------
# Public endpoints (no auth)
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "version": "6.0.0"}


@app.get("/")
async def root():
    return {"version": "6.0.0", "name": "Agentic Harness Bridge v6"}


@app.post("/auth/token")
async def auth_token(req: TokenRequest):
    """Generate a JWT token. Requires JWT_SECRET to be set."""
    try:
        token = create_token(req.subject, req.expires_minutes)
        return {"token": token, "type": "bearer", "expires_in": req.expires_minutes * 60}
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


# ---------------------------------------------------------------------------
# SSE Streaming
# ---------------------------------------------------------------------------

@app.get("/stream/trace/{trace_id}")
async def stream_trace(trace_id: str):
    """SSE stream for real-time trace updates."""
    import asyncio

    async def _event_generator():
        stages = ["pending", "running", "running", "done"]
        for stage in stages:
            payload = json.dumps({
                "trace_id": trace_id,
                "status": stage,
                "timestamp": core.now(),
            })
            yield f"data: {payload}\n\n"
            await asyncio.sleep(0.05)
        yield "event: close\ndata: end\n\n"

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


# ---------------------------------------------------------------------------
# Base Patterns (auth required if JWT_SECRET is set)
# ---------------------------------------------------------------------------

@app.post("/pattern/chain")
async def pattern_chain(req: ChainRequest, auth: dict = Depends(verify_token)):
    """Prompt Chaining — sequential LLM calls."""
    trace = core.Trace(pattern="chain", input_payload=req.model_dump())
    results: list[str] = []
    model_calls = 0
    total_cost = 0.0

    context = ""
    for prompt in req.prompts:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"{context}\n{prompt}".strip()},
        ]
        resp = await core.azure_complete(messages, temperature=req.temperature)
        results.append(resp)
        context = resp
        model_calls += 1
        total_cost += 0.002

    trace.status = "done"
    trace.model_calls = model_calls
    trace.cost_usd = total_cost
    trace.output_payload = {"results": results}
    return {"trace": trace.model_dump(), "results": results}


@app.post("/pattern/route")
async def pattern_route(req: RouteRequest, auth: dict = Depends(verify_token)):
    """Routing — classify then dispatch."""
    trace = core.Trace(pattern="route", input_payload=req.model_dump())

    route_names = list(req.routes.keys())
    classify_msg = [
        {
            "role": "system",
            "content": f"Classify the input into one of: {', '.join(route_names)}. Reply with only the route name.",
        },
        {"role": "user", "content": req.input_text},
    ]
    selected = (await core.azure_complete(classify_msg, temperature=0.2)).strip()
    trace.model_calls = 1
    trace.cost_usd = 0.002

    if selected not in req.routes:
        selected = route_names[0] if route_names else "unknown"

    route_msg = [
        {"role": "system", "content": req.routes.get(selected, "")},
        {"role": "user", "content": req.input_text},
    ]
    output = await core.azure_complete(route_msg)
    trace.model_calls += 1
    trace.cost_usd += 0.002

    trace.status = "done"
    trace.output_payload = {"selected_route": selected, "output": output}
    return {"trace": trace.model_dump(), "selected_route": selected, "output": output}


@app.post("/pattern/parallel")
async def pattern_parallel(req: ParallelRequest, auth: dict = Depends(verify_token)):
    """Parallelization — fan-out LLM calls."""
    import asyncio

    trace = core.Trace(pattern="parallel", input_payload=req.model_dump())

    async def _run(task: str) -> str:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": task},
        ]
        return await core.azure_complete(messages, temperature=req.temperature)

    results = await asyncio.gather(*[_run(t) for t in req.tasks])
    trace.status = "done"
    trace.model_calls = len(req.tasks)
    trace.cost_usd = len(req.tasks) * 0.002
    trace.output_payload = {"results": results}
    return {"trace": trace.model_dump(), "results": results}


@app.post("/pattern/orchestrate")
async def pattern_orchestrate(req: OrchestrateRequest, auth: dict = Depends(verify_token)):
    """Orchestrator-Workers with optional GapSolver pre-analysis."""
    import asyncio

    trace = core.Trace(pattern="orchestrate", input_payload=req.model_dump())
    model_calls = 0
    total_cost = 0.0

    if req.pre_analyze:
        pre = await discover_gaps(req.objective)
        model_calls += pre["trace"].get("model_calls", 0)
        total_cost += pre["trace"].get("cost_usd", 0.0)

    plan_msg = [
        {
            "role": "system",
            "content": "Break the objective into subtasks. Reply as JSON list of strings.",
        },
        {"role": "user", "content": req.objective},
    ]
    plan_raw = await core.azure_complete(plan_msg, temperature=0.3)
    model_calls += 1
    total_cost += 0.002

    subtasks = core._parse_subtasks(plan_raw)

    async def _worker(task: str) -> str:
        messages = [
            {"role": "system", "content": "You are a worker. Complete the subtask."},
            {"role": "user", "content": task},
        ]
        return await core.azure_complete(messages)

    worker_results = await asyncio.gather(*[_worker(t) for t in subtasks])
    model_calls += len(subtasks)
    total_cost += len(subtasks) * 0.002

    synth_msg = [
        {
            "role": "system",
            "content": "Synthesize worker outputs into a final answer.",
        },
        {"role": "user", "content": "\n\n".join(worker_results)},
    ]
    final = await core.azure_complete(synth_msg)
    model_calls += 1
    total_cost += 0.002

    trace.status = "done"
    trace.model_calls = model_calls
    trace.cost_usd = total_cost
    trace.output_payload = {"subtasks": subtasks, "worker_results": worker_results, "final": final}
    return {
        "trace": trace.model_dump(),
        "subtasks": subtasks,
        "worker_results": worker_results,
        "final": final,
    }


@app.post("/pattern/evaluate_optimize")
async def pattern_evaluate_optimize(req: EvalOptimizeRequest, auth: dict = Depends(verify_token)):
    """Evaluator-Optimizer loop."""
    trace = core.Trace(pattern="evaluate_optimize", input_payload=req.model_dump())
    draft = ""
    model_calls = 0
    total_cost = 0.0

    for i in range(1, req.max_iterations + 1):
        gen_msg = [
            {"role": "system", "content": "Generate content based on the prompt."},
            {"role": "user", "content": req.prompt},
        ]
        draft = await core.azure_complete(gen_msg)
        model_calls += 1
        total_cost += 0.002

        eval_prompt = (
            f"Score 0-1 against rubric: {req.rubric}. "
            'Reply JSON: {"score": float, "feedback": str}'
        )
        eval_msg = [
            {"role": "system", "content": eval_prompt},
            {"role": "user", "content": draft},
        ]
        eval_raw = await core.azure_complete(eval_msg, temperature=0.2)
        model_calls += 1
        total_cost += 0.005

        try:
            eval_res = json.loads(eval_raw)
        except Exception:
            eval_res = {"score": 0.0, "feedback": "parse error"}

        trace.output_payload = {"iteration": i, "draft": draft, "score": eval_res.get("score", 0.0)}
        if eval_res.get("score", 0.0) >= 0.85:
            break

    trace.status = "done"
    trace.model_calls = model_calls
    trace.cost_usd = total_cost
    return {
        "trace": trace.model_dump(),
        "draft": draft,
        "score": trace.output_payload.get("score", 0.0),
        "iterations": trace.output_payload.get("iteration", 1),
    }


@app.post("/pattern/react")
async def pattern_react(req: ReActRequest, auth: dict = Depends(verify_token)):
    """ReAct pattern endpoint."""
    result = await hunt(req.query, max_model_calls=req.max_model_calls)
    return result


@app.post("/pattern/reflect")
async def pattern_reflect(req: ReflectRequest, auth: dict = Depends(verify_token)):
    """Reflection — critique then rewrite."""
    trace = core.Trace(pattern="reflect", input_payload=req.model_dump())

    critique_prompt = (
        f"Critique this draft against criteria: {', '.join(req.criteria)}. "
        'Reply JSON: {"issues": [str], "score": 0-1}'
    )
    critique_msg = [
        {"role": "system", "content": critique_prompt},
        {"role": "user", "content": req.draft},
    ]
    critique_raw = await core.azure_complete(critique_msg, temperature=0.3)
    trace.model_calls = 1
    trace.cost_usd = 0.002

    try:
        critique = json.loads(critique_raw)
    except Exception:
        critique = {"issues": [], "score": 0.5}

    rewrite_msg = [
        {
            "role": "system",
            "content": f"Rewrite the draft addressing these issues: {critique.get('issues', [])}",
        },
        {"role": "user", "content": req.draft},
    ]
    rewritten = await core.azure_complete(rewrite_msg)
    trace.model_calls += 1
    trace.cost_usd += 0.002

    trace.status = "done"
    trace.output_payload = {"critique": critique, "rewritten": rewritten}
    return {
        "trace": trace.model_dump(),
        "critique": critique,
        "rewritten": rewritten,
    }


# ---------------------------------------------------------------------------
# Domain Bridges (auth required if JWT_SECRET is set)
# ---------------------------------------------------------------------------

@app.post("/nexus/enrich")
async def nexus_enrich(req: NexusEnrichRequest, auth: dict = Depends(verify_token)):
    lead = core.Lead(**req.model_dump())
    return await enrich_lead(lead)


@app.post("/gapclaw/hunt")
async def gapclaw_hunt(req: ReActRequest, auth: dict = Depends(verify_token)):
    return await hunt(req.query, max_model_calls=req.max_model_calls)


@app.post("/sara/generate")
async def sara_generate(req: SaraGenerateRequest, auth: dict = Depends(verify_token)):
    return await generate_script(req.topic, req.rubric, req.max_iterations)


@app.post("/gapsolver/discover")
async def gapsolver_discover(req: GapSolverDiscoverRequest, auth: dict = Depends(verify_token)):
    return await discover_gaps(req.industry, req.location, req.top_n)


# ---------------------------------------------------------------------------
# Grok (xAI) — native SDK: chat, vision, voice, function-calling
# ---------------------------------------------------------------------------

# Circuit breaker for external LLM calls
grok_circuit = CircuitBreaker(failure_threshold=5, recovery_timeout=30)

@grok_circuit
async def grok_chat_with_circuit(messages: list[dict]) -> dict:
    if os.getenv("XAI_API_KEY"):
        return await grok_chat(messages)
    return await grok_chat_free(messages)


@app.post("/grok/chat")
async def grok_chat_endpoint(messages: list[dict], auth: dict = Depends(verify_token)):
    return await grok_chat_with_circuit(messages)


@app.post("/grok/vision")
async def grok_vision_endpoint(
    img: UploadFile = File(...), prompt: str = Form(...), auth: dict = Depends(verify_token)
):
    import base64
    b64 = base64.b64encode(await img.read()).decode()
    return await grok_vision(
        [{"role": "user", "content": prompt}],
        f"data:image/jpeg;base64,{b64}",
    )


@app.post("/grok/voice/transcribe")
async def grok_voice_transcribe_endpoint(
    audio: UploadFile = File(...), auth: dict = Depends(verify_token)
):
    import base64
    b64 = base64.b64encode(await audio.read()).decode()
    return await grok_voice_transcribe(b64)


@app.post("/grok/voice/speak")
async def grok_voice_speak_endpoint(text: str = Form(...), auth: dict = Depends(verify_token)):
    return await grok_voice_speak(text)


# ---------------------------------------------------------------------------
# Azure OpenAI endpoints
# ---------------------------------------------------------------------------

class AzureChatRequest(BaseModel):
    messages: list[dict]
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 2048


class AzureEmbeddingsRequest(BaseModel):
    input: str | list[str]
    model: str = "text-embedding-3-large"


@app.post("/azure/chat")
async def azure_chat_endpoint(req: AzureChatRequest, auth: dict = Depends(verify_token)):
    return await azure_chat(req.messages, req.model, req.temperature, req.max_tokens)


@app.post("/azure/embeddings")
async def azure_embeddings_endpoint(req: AzureEmbeddingsRequest, auth: dict = Depends(verify_token)):
    return await azure_embeddings(req.input, req.model)


# ---------------------------------------------------------------------------
# Free provider endpoints (auto-fallback or explicit)
# ---------------------------------------------------------------------------

@app.post("/grok/free/chat")
async def grok_free_chat_endpoint(
    messages: list[dict],
    provider: str = "freetheai",
    auth: dict = Depends(verify_token),
):
    """Explicit free provider chat (freetheai|puter)."""
    return await grok_chat_free(messages, provider=provider)


@app.get("/grok/free/providers")
async def grok_free_providers_endpoint(auth: dict = Depends(verify_token)):
    """List configured free providers and their status."""
    import os
    status = {}
    for name, cfg in FREE_PROVIDERS.items():
        key = os.getenv(cfg["key_env"])
        status[name] = {
            "configured": bool(key),
            "key_preview": key[:10] + "..." if key else None,
            "base_url": cfg["base_url"],
            "models": cfg["models"],
        }
    return {"providers": status}


# ---------------------------------------------------------------------------
# Multi-model swarm — parallel queries across all free providers
# ---------------------------------------------------------------------------

@app.post("/swarm")
async def swarm_endpoint(messages: list[dict], auth: dict = Depends(verify_token)):
    """Run same prompt across all free providers in parallel."""
    return await swarm_chat(messages)


# ---------------------------------------------------------------------------
# Health checks — registry-based
# ---------------------------------------------------------------------------

# Register default health checks
async def _check_redis() -> dict:
    try:
        import redis.asyncio as redis
        client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)
        await client.ping()
        await client.close()
        return {"healthy": True}
    except Exception as e:
        return {"healthy": False, "error": str(e)}


async def _check_ollama() -> dict:
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://127.0.0.1:11434/api/tags")
            return {"healthy": resp.status_code == 200}
    except Exception as e:
        return {"healthy": False, "error": str(e)}


async def _check_grok() -> dict:
    has_key = bool(os.getenv("XAI_API_KEY") or os.getenv("FREETHEAI_API_KEY") or os.getenv("PUTER_AUTH_TOKEN"))
    return {"healthy": has_key, "configured": has_key}


health_registry.register("redis", _check_redis)
health_registry.register("ollama", _check_ollama)
health_registry.register("grok", _check_grok)


@app.get("/health/full")
async def full_health_check():
    """Comprehensive health check with all registered checks."""
    results = await health_registry.run_all()
    overall = "healthy" if all(r["status"] == "healthy" for r in results.values()) else "degraded"
    return {"status": overall, "checks": results, "request_id": get_request_id()}


# ---------------------------------------------------------------------------
# Live dashboard data — health, metrics, grok session, repo status
# ---------------------------------------------------------------------------

@app.get("/dashboard")
async def dashboard_endpoint(auth: dict = Depends(verify_token)):
    """Unified dashboard data for web console."""
    import os
    from api.unified_system import UnifiedSystem
    from api.repo_registry import summary as repo_summary
    
    system = UnifiedSystem()
    health = await system.check_all_health()
    
    # Grok session log
    try:
        with open("/tmp/opencode/grok_5hr.log") as f:
            grok_log = f.read()[-3000:]
    except FileNotFoundError:
        grok_log = "(no session)"
    
    # Repo summary
    repos = repo_summary()
    
    return {
        "health": health,
        "grok_session_log": grok_log,
        "repos": repos,
        "free_providers": {name: cfg for name, cfg in FREE_PROVIDERS.items()},
        "uptime": "live",
    }


# ---------------------------------------------------------------------------
# Recommended upgrade repos registry (3 tiers, curated 2026-08-15)
# ---------------------------------------------------------------------------

@app.get("/repos")
async def repos_endpoint(tier: str | None = None):
    return list_repos(tier)


@app.get("/repos/summary")
async def repos_summary_endpoint():
    return repo_summary()


# ---------------------------------------------------------------------------
# 5-hour Grok autonomous session + surprise: live self-analysis
# ---------------------------------------------------------------------------

_grok_session_task: asyncio.Task | None = None


@app.post("/grok/session/start")
async def grok_session_start(auth: dict = Depends(verify_token)):
    global _grok_session_task
    if _grok_session_task and not _grok_session_task.done():
        return {"status": "already_running", "task": "active"}
    from api.grok_5hr import run as _run_5hr
    _grok_session_task = asyncio.create_task(_run_5hr())
    return {"status": "started", "duration_hours": 5}


@app.get("/grok/session/log")
async def grok_session_log(auth: dict = Depends(verify_token)):
    try:
        with open("/tmp/opencode/grok_5hr.log") as f:
            return {"log": f.read()[-4000:]}
    except FileNotFoundError:
        return {"log": "(no session yet)"}


@app.post("/grok/analyze")
async def grok_analyze(snapshot: dict, auth: dict = Depends(verify_token)):
    """Surprise: ask Grok to critique the current system snapshot and rank upgrades."""
    messages = [
        {"role": "system", "content": "You are SAHIIX Grok. Given a system snapshot, return the top 3 upgrades as a ranked list with one-line justification each."},
        {"role": "user", "content": f"Snapshot: {snapshot}"},
    ]
    return await grok_chat(messages)


# ---------------------------------------------------------------------------
# Observability
# ---------------------------------------------------------------------------

@app.get("/traces/escalated")
async def traces_escalated(auth: dict = Depends(verify_token)):
    return {"escalated": [], "count": 0}
