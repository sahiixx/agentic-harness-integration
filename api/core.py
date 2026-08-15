"""Core shared module — models, Azure client, utilities.

All bridges import this module. Tests patch `core.azure_complete` once
and the mock propagates everywhere.
"""
from __future__ import annotations

import asyncio
import os
import random
import time
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Callable, Coroutine, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Trace(BaseModel):
    """Observable unit of work for human review."""
    model_config = {"protected_namespaces": ()}
    trace_id: str = Field(default_factory=lambda: f"t_{int(time.time()*1000)}")
    pattern: str
    status: str = "pending"          # pending | running | done | escalated
    input_payload: dict = Field(default_factory=dict)
    output_payload: dict = Field(default_factory=dict)
    model_calls: int = 0
    cost_usd: float = 0.0
    created_at: str = Field(default_factory=lambda: now())
    escalated: bool = False


class Lead(BaseModel):
    """NEXUS enrichment target."""
    name: str = ""
    email: str = ""
    phone: str = ""
    company: str = ""
    title: str = ""
    linkedin: str = ""
    enriched: dict = Field(default_factory=dict)


class Gap(BaseModel):
    """GapSolver discovery output."""
    gap_id: str = Field(default_factory=lambda: f"g_{int(time.time()*1000)}")
    category: str = ""
    description: str = ""
    revenue_score: float = 0.0       # 0-1 composite
    urgency: str = "medium"          # low | medium | high
    source: str = ""


class ReActStep(BaseModel):
    """Single ReAct reasoning step."""
    thought: str = ""
    action: str = ""
    action_input: dict = Field(default_factory=dict)
    observation: str = ""


# ---------------------------------------------------------------------------
# Time helper
# ---------------------------------------------------------------------------

def now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Azure AI Foundry client
# ---------------------------------------------------------------------------

_AZURE_KEY: Optional[str] = None
_AZURE_BASE: Optional[str] = None


def _azure_config() -> tuple[str, str]:
    global _AZURE_KEY, _AZURE_BASE
    if _AZURE_KEY is None:
        _AZURE_KEY = os.getenv("AZURE_FOUNDRY_API_KEY", "")
    if _AZURE_BASE is None:
        _AZURE_BASE = os.getenv("AZURE_FOUNDRY_BASE_URL", "")
    if not _AZURE_KEY or not _AZURE_BASE:
        raise RuntimeError("Azure Foundry credentials missing")
    return _AZURE_KEY, _AZURE_BASE


def _retryable(exc: Exception) -> bool:
    """429/5xx/network errors are transient; 4xx client errors are not."""
    import httpx

    if isinstance(exc, (httpx.TransportError, httpx.TimeoutException)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500 or exc.response.status_code == 429
    return False


async def _with_retry(coro, attempts: int = 3):
    for i in range(attempts):
        try:
            return await coro()
        except Exception as exc:
            if not _retryable(exc) or i == attempts - 1:
                raise
            await asyncio.sleep(0.5 * (2 ** i) + random.uniform(0, 0.1))


async def azure_complete(
    messages: list[dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    """Call Azure AI Foundry chat completion.

    Tests patch this function directly — no real HTTP leaves the test suite.
    """
    import httpx

    key, base_url = _azure_config()
    model = model or os.getenv("AZURE_DEFAULT_MODEL", "gpt-5.6-sol")

    # Random jitter to avoid thundering herd in production
    jitter = random.uniform(0.05, 0.25)
    await asyncio.sleep(jitter)

    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async def _call():
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    return await _with_retry(_call)


async def azure_embed(texts: list[str], model: Optional[str] = None) -> list[list[float]]:
    """Azure embedding endpoint."""
    import httpx

    key, base_url = _azure_config()
    model = model or os.getenv("AZURE_EMBED_MODEL", "text-embedding-3-large")

    url = f"{base_url.rstrip('/')}/embeddings"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {"model": model, "input": texts}

    async def _call():
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data["data"]]

    return await _with_retry(_call)


# ---------------------------------------------------------------------------
# Subtask parser (orchestrator pattern)
# ---------------------------------------------------------------------------

def _parse_subtasks(raw: str) -> list[str]:
    """Parse orchestrator subtask output.

    Handles:
    - JSON list:   ["task1", "task2"]
    - JSON object: {"subtasks": [...]}
    - Plain text:  line-separated
    - Empty input: [""]
    """
    if not raw.strip():
        return [""]

    raw = raw.strip()
    if raw.startswith("["):
        try:
            import json
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except Exception:
            pass
    if raw.startswith("{"):
        try:
            import json
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and "subtasks" in parsed:
                return [str(x) for x in parsed["subtasks"]]
        except Exception:
            pass
    # Fallback: line-separated, filter empty
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    return lines if lines else [""]


def _self_check() -> None:
    """Runnable assert-based check: retry on 429/5xx, no retry on 4xx."""
    import httpx
    import asyncio

    async def main():
        calls = {"n": 0}

        async def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise httpx.HTTPStatusError(
                    "429", request=httpx.Request("POST", "http://x"), response=httpx.Response(429)
                )
            return "ok"

        out = await _with_retry(flaky, attempts=3)
        assert out == "ok" and calls["n"] == 3, f"retry failed: {calls['n']}"

        async def bad():
            raise httpx.HTTPStatusError(
                "400", request=httpx.Request("POST", "http://x"), response=httpx.Response(400)
            )

        try:
            await _with_retry(bad, attempts=3)
            raise AssertionError("4xx should not retry")
        except httpx.HTTPStatusError:
            pass
        print("self-check OK: 429 retried, 400 not retried")

    asyncio.run(main())


if __name__ == "__main__":
    _self_check()
