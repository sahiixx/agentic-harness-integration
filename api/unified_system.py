"""
SAHIIX Unified System — single orchestration layer tying together:
- Agentic Harness v6 (FastAPI + Next.js console)
- SAHIIX OS (Hermes @ 8765, WA bridge @ 8766, Telegram @He3rmessbot)
- Real-estate pipeline (Phase 11-15, 2.5, 2.6)
- Orchestrator framework (run.py patterns: chain, route, parallel, fallback, self-heal)
- xAI Grok native SDK (grok-4.6 + tools: web_search, x_search, code_execution)
- 5hr autonomous Grok improvement loop
- 13-repo upgrade registry (3 tiers)
- PM2 fleet management (ecosystem.sahiixx.config.js)
- Self-heal / ops-agent patterns
- Telegram throttled notifications (tg_throttle)
- Cloudflare tunnel public access
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Coroutine, TypeVar

import httpx

# ─── Local imports ───
from api.core import retry_async
from api.grok_bridge import grok_chat, grok_voice_transcribe, grok_voice_speak
from api.repo_registry import list_repos, summary as repo_summary

# ─── Self-contained orchestrator patterns (no external dependency) ───
T = TypeVar("T")


def chain(*fns: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
    """Chain: f1 -> f2 -> f3 ..."""
    async def _run(x: Any = None) -> T:
        result = x
        for fn in fns:
            if result is None:
                result = await fn()
            elif isinstance(result, dict):
                result = await fn(result)
            else:
                result = await fn(result)
        return result
    return _run


async def parallel(*fns: Callable[..., Coroutine[Any, Any, T]]) -> list[T]:
    """Parallel: run all concurrently, return list of results."""
    return await asyncio.gather(*[fn() for fn in fns])


async def fallback(*fns: Callable[..., Coroutine[Any, Any, T]]) -> T:
    """Fallback: try each until one succeeds."""
    last_exc = None
    for fn in fns:
        try:
            return await fn()
        except Exception as e:
            last_exc = e
    raise last_exc or RuntimeError("all fallbacks failed")


def route(condition: Callable[[Any], bool], on_true: Callable, on_false: Callable) -> Callable:
    """Route: conditional branch."""
    async def _run(x: Any) -> Any:
        return await (on_true(x) if condition(x) else on_false(x))
    return _run

# ─── Constants ───
SAHIIX_OS_BASE = os.getenv("SAHIIX_OS_BASE", "http://127.0.0.1:8765")
REAL_ESTATE_BASE = os.getenv("REAL_ESTATE_BASE", "http://127.0.0.1:8001")
ORCHESTRATOR_BASE = os.getenv("ORCHESTRATOR_BASE", "http://127.0.0.1:8002")
HARNESS_API_BASE = os.getenv("HARNESS_API_BASE", "http://127.0.0.1:8000")
PUBLIC_TUNNEL = os.getenv("PUBLIC_TUNNEL", "https://include-finished-emotional-glenn.trycloudflare.com")

GROK_MODEL = os.getenv("GROK_MODEL", "grok-4.6")
GROK_SESSION_LOG = "/tmp/opencode/grok_5hr.log"
GROK_SESSION_DURATION = 5 * 3600
GROK_SESSION_INTERVAL = 300

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


@dataclass
class SystemHealth:
    name: str
    url: str
    status: str = "unknown"
    last_check: float = 0
    metadata: dict = field(default_factory=dict)


class UnifiedSystem:
    """
    Single orchestration layer for the entire SAHIIX fleet.
    Runs as a background task under PM2 (unified-system).
    """

    def __init__(self):
        self.health: dict[str, SystemHealth] = {}
        self.grok_session_task: asyncio.Task | None = None
        self.running = False

        # Register all known subsystems
        self._register_subsystems()

    def _register_subsystems(self) -> None:
        subsystems = [
            ("harness-api", f"{HARNESS_API_BASE}/health"),
            ("harness-web", f"{PUBLIC_TUNNEL}"),
            ("hermes-mcp", f"{SAHIIX_OS_BASE}/health"),
            ("hermes-telegram", f"{SAHIIX_OS_BASE}/tg/health"),
            ("wa-bridge", f"{SAHIIX_OS_BASE}/wa/health"),
            ("real-estate", f"{REAL_ESTATE_BASE}/health"),
            ("orchestrator", f"{ORCHESTRATOR_BASE}/health"),
            ("genx-dashboard", "http://127.0.0.1:8090/health"),
            ("lead-capture", "http://127.0.0.1:8003/health"),
            ("ops-agent", "http://127.0.0.1:8004/health"),
            ("memory-broker", "http://127.0.0.1:8790/health"),
            ("research-agent", "http://127.0.0.1:8791/health"),
            ("orchestrator-agent", "http://127.0.0.1:8792/health"),
        ]
        for name, url in subsystems:
            self.health[name] = SystemHealth(name=name, url=url)

    # ─── Health monitoring ───
    async def check_all_health(self) -> dict[str, Any]:
        async def check_one(h: SystemHealth) -> SystemHealth:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    r = await client.get(h.url)
                    h.status = "healthy" if r.status_code == 200 else f"degraded:{r.status_code}"
                    h.metadata = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            except Exception as e:
                h.status = f"down:{type(e).__name__}"
            h.last_check = time.time()
            return h

        await asyncio.gather(*[check_one(h) for h in self.health.values()])
        return {k: {"status": v.status, "last_check": v.last_check, "meta": v.metadata} for k, v in self.health.items()}

    # ─── Self-heal via PM2 ───
    async def self_heal(self, health: dict[str, Any]) -> list[str]:
        restarted = []
        for name, info in health.items():
            if info["status"].startswith("down") or info["status"].startswith("degraded"):
                try:
                    subprocess.run(["pm2", "restart", name], check=True, capture_output=True, timeout=30)
                    restarted.append(name)
                    await self._notify(f"🔧 Self-heal: restarted `{name}` ({info['status']})")
                except Exception as e:
                    await self._notify(f"❌ Self-heal failed for `{name}`: {e}")
        return restarted

    # ─── Grok 5hr autonomous improvement (Grok 4.6: xhigh reasoning, prompt_cache_key, Priority Processing) ───
    async def start_grok_session(self) -> dict:
        if self.grok_session_task and not self.grok_session_task.done():
            return {"status": "already_running"}

        async def _run():
            cache_key = f"sahix-unified-{int(time.time())}"  # unique per session for 500k ctx caching
            with open(GROK_SESSION_LOG, "a") as f:
                f.write(f"[{datetime.now().isoformat()}] 5hr Grok session START (cache_key={cache_key})\n")
            start = time.time()
            turn = 0
            while time.time() - start < GROK_SESSION_DURATION:
                turn += 1
                messages = [
                    {"role": "system", "content": self._grok_system_prompt()},
                    {"role": "user", "content": f"Turn {turn}: propose ONE concrete, shippable improvement to the SAHIIX Unified System. Include file path and code sketch."},
                ]
                try:
                    # Use Grok 4.6 features: xhigh reasoning for complex improvements, prompt_cache_key for 500k ctx, priority for speed
                    res = await grok_chat(
                        messages,
                        model=GROK_MODEL,
                        tools=True,
                        reasoning_effort="xhigh",      # NEW: deepest reasoning for system design
                        prompt_cache_key=cache_key,    # NEW: cache 500k context across turns
                        priority=True,                 # NEW: Priority Processing (2x price, faster)
                    )
                    content = res.get("content", str(res))
                    line = f"[{datetime.now().isoformat()}] turn {turn}: {str(content)[:280]}\n"
                except Exception as e:
                    line = f"[{datetime.now().isoformat()}] turn {turn} ERROR: {e}\n"
                with open(GROK_SESSION_LOG, "a") as f:
                    f.write(line)
                await asyncio.sleep(GROK_SESSION_INTERVAL)
            with open(GROK_SESSION_LOG, "a") as f:
                f.write(f"[{datetime.now().isoformat()}] 5hr Grok session END ({turn} turns)\n")

        self.grok_session_task = asyncio.create_task(_run())
        return {"status": "started", "duration_hours": 5, "model": GROK_MODEL, "features": ["xhigh", "prompt_cache", "priority"]}

    def _grok_system_prompt(self) -> str:
        return (
            "You are SAHIIX Grok, the autonomous improvement agent for the Unified System. "
            "Context: FastAPI harness (v6) on Termux/Android, PM2 fleet (13 apps), "
            "SAHIIX OS (Hermes MCP/Telegram/WA), Real-estate pipeline (Phases 11-15, 2.5/2.6), "
            "Orchestrator framework (chain/route/parallel/fallback/self-heal), "
            "xAI SDK (grok-4.6, tools: web_search, x_search, code_execution, reasoning_effort=xhigh, prompt_cache_key, Priority Processing), "
            "13-repo upgrade registry (3 tiers, latest: AgentScope 2.0.6, crewAI 1.15.16, Next.js 16.3.1), "
            "Cloudflare tunnel, Telegram throttling. "
            "Each turn: output ONE concrete improvement with file path + minimal code sketch. "
            "Prioritize: self-heal coverage, Grok tool-use, repo integration, observability, "
            "and removing single points of failure."
        )

    async def get_grok_log(self) -> str:
        try:
            with open(GROK_SESSION_LOG) as f:
                return f.read()[-5000:]
        except FileNotFoundError:
            return "(no session yet)"

    # ─── Repo upgrade proposals ───
    async def propose_upgrades(self) -> list[dict]:
        """Ask Grok to rank the 13 repos by impact for the current system."""
        snapshot = {
            "health": await self.check_all_health(),
            "repos": repo_summary(),
            "grok_log": await self.get_grok_log(),
        }
        messages = [
            {"role": "system", "content": "Rank the upgrade repos by impact for THIS system. Return top 3 with one-line justification each."},
            {"role": "user", "content": f"Snapshot: {json.dumps(snapshot, default=str)[:3000]}"},
        ]
        res = await grok_chat(messages, model=GROK_MODEL, tools=True)
        return [{"proposal": res.get("content", str(res))}]

    # ─── Orchestrator-pattern workflows ───
    async def run_full_health_cycle(self) -> dict:
        """Chain: check health → self-heal → notify → log."""
        async def check():
            return await self.check_all_health()

        async def heal(health):
            return await self.self_heal(health)

        async def notify(result):
            healed = result.get("restarted", [])
            if healed:
                await self._notify(f"✅ Health cycle: healed {len(healed)} services: {', '.join(healed)}")
            return {"health": result.get("health"), "healed": healed}

        async def log(result):
            with open("/tmp/opencode/unified_health.log", "a") as f:
                f.write(f"[{datetime.now().isoformat()}] {json.dumps(result, default=str)}\n")
            return result

        return await chain(check, heal, notify, log)()

    async def run_parallel_research(self, query: str) -> dict:
        """Parallel: research-agent + Grok + local repo registry."""
        async def research():
            async with httpx.AsyncClient(timeout=30) as c:
                r = await c.post(f"http://127.0.0.1:8791/research", json={"query": query})
                return r.json()

        async def grok():
            res = await grok_chat([{"role": "user", "content": f"Research: {query}"}], model=GROK_MODEL, tools=True)
            return {"grok": res.get("content", str(res))}

        async def registry():
            return {"repos": repo_summary()}

        return await parallel(research, grok, registry)()

    # ─── Telegram notify (throttled via tg_throttle pattern) ───
    async def _notify(self, text: str) -> None:
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            return
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                await c.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"},
                )
        except Exception:
            pass  # best effort

    # ─── Main loop ───
    async def run_forever(self, health_interval: int = 120) -> None:
        """Main unified loop: health cycle every 2min, Grok session on demand."""
        self.running = True
        await self._notify("🚀 Unified System online — all 13 subsystems registered")
        while self.running:
            try:
                await self.run_full_health_cycle()
            except Exception as e:
                await self._notify(f"⚠️ Health cycle error: {e}")
            await asyncio.sleep(health_interval)

    def stop(self) -> None:
        self.running = False
        if self.grok_session_task:
            self.grok_session_task.cancel()


# ─── CLI entry ───
async def main():
    system = UnifiedSystem()
    try:
        await system.run_forever()
    except KeyboardInterrupt:
        system.stop()


if __name__ == "__main__":
    asyncio.run(main())