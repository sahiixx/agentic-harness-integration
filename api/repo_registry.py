"""Recommended upgrade repos — 3 tiers, curated from live research (2026-08-15).

Tier 1: xAI native (Grok integration)
Tier 2: Autonomous agent frameworks (self-improving, 24/7)
Tier 3: Specialized power-ups (memory, TS, visual builders)

Updated with Aug 2026 releases:
- xAI SDK 1.18.0, Grok 4.6 (xhigh reasoning, 500k ctx, prompt caching)
- AgentScope v2.0.6 (MCP/Skill Hubs, Apple Container, Feishu/Discord)
- crewAI 1.15.16 (execution context UUID, telemetry, IBM Db2)
- Next.js 16.3.1 (Instant Navigations, July security patches)
"""
from __future__ import annotations

from typing import Any

REPO_TIERS: dict[str, list[dict[str, Any]]] = {
    "tier1_xai_native": [
        {
            "name": "xai-sdk-python",
            "repo": "xai-org/xai-sdk-python",
            "url": "https://github.com/xai-org/xai-sdk-python",
            "version": "1.18.0",
            "why": "Official Python SDK: async/sync, streaming, grok-4.6, web/X search, code interpreter, context compaction, file attachments, function calling, reasoning_effort (xhigh), prompt_cache_key, Priority Processing.",
            "integrates_with": "harness /grok/* endpoints (native SDK replaces OpenAI-compatible stub)",
            "status": "integrated",
            "updated": "2026-08-12",
        },
        {
            "name": "grok-build",
            "repo": "xai-org/grok-build",
            "url": "https://github.com/xai-org/grok-build",
            "version": "latest",
            "why": "Official Grok Build CLI/TUI (Rust). ACP protocol for embedding, headless mode, subagents, MCP/skills/plugins, worktree isolation. 2x included usage for Grok 4.6 first week.",
            "integrates_with": "headless agent builds / CI pipelines",
            "status": "documented",
        },
        {
            "name": "grok-bot",
            "repo": "xai-org/grok-bot",
            "url": "https://github.com/xai-org/grok-bot",
            "version": "latest",
            "why": "Cloud AI teammates. Long-running agents on persistent cloud computer, messaging, approvals, connectors, routines, A2A protocol.",
            "integrates_with": "cloud agent delegation via grok_bot_delegate()",
            "status": "documented",
        },
    ],
    "tier2_agent_frameworks": [
        {
            "name": "agentscope",
            "repo": "agentscope-ai/agentscope",
            "url": "https://github.com/agentscope-ai/agentscope",
            "stars": "~15K",
            "version": "2.0.6 (2026-08-07)",
            "why": "Agent Service (FastAPI + Web UI), multi-tenancy, RAG service, MCP/Skill Hubs (GitHub MCP Registry, ClawHub), distributed memory (Mem0/ReMe/ReMe), workspace sandboxes (Docker/E2B/Daytona/K8s/Apple Container), permission/HITL, Feishu/Discord channels, leader-worker teams, shadcn Web UI.",
            "integrates_with": "replaces custom orchestrator patterns with managed agent service",
            "status": "documented",
        },
        {
            "name": "agent-framework",
            "repo": "microsoft/agent-framework",
            "url": "https://github.com/microsoft/agent-framework",
            "stars": "new",
            "why": "Unified AutoGen + Semantic Kernel successor. Graph workflows, Foundry hosting, OpenTelemetry, declarative YAML agents, skills, durable execution.",
            "integrates_with": "durable graph workflows + observability",
            "status": "documented",
        },
        {
            "name": "crewAI",
            "repo": "crewaiinc/crewAI",
            "url": "https://github.com/crewaiinc/crewAI",
            "stars": "100K+",
            "version": "1.15.16 (2026-08-14)",
            "why": "Role-based crews + Flows (event-driven). Execution context management with UUID, telemetry tracking, enterprise account linking, IBM Db2 search tool, Frontend guides for CopilotKit/AG-UI.",
            "integrates_with": "role-based multi-agent crews",
            "status": "documented",
        },
        {
            "name": "agno",
            "repo": "agno-agi/agno",
            "url": "https://github.com/agno-agi/agno",
            "stars": "29K",
            "why": "Full-stack: memory, reasoning, vector DB, multimodal, agentic search, MCP.",
            "integrates_with": "multimodal agent backbone",
            "status": "documented",
        },
        {
            "name": "openai-agents",
            "repo": "openai-agents/agents",
            "url": "https://github.com/openai/openai-agents-python",
            "stars": "27K",
            "why": "Lightweight, 100+ models, tracing, guardrails, MCP, handoffs.",
            "integrates_with": "model-agnostic agent layer",
            "status": "documented",
        },
        {
            "name": "langgraph",
            "repo": "langchain-ai/langgraph",
            "url": "https://github.com/langchain-ai/langgraph",
            "stars": "33K",
            "version": "1.2.111 (2026-08-11)",
            "why": "Stateful cyclic graphs, human-in-the-loop, LangSmith observability. trace_policy on add_node, type-hinted v3 stream_events, native projections.",
            "integrates_with": "stateful agent graphs",
            "status": "documented",
        },
    ],
    "tier3_specialized": [
        {
            "name": "letta",
            "repo": "letta-ai/letta",
            "url": "https://github.com/letta-ai/letta",
            "stars": "ex-MemGPT",
            "why": "Stateful long-term memory agents.",
            "integrates_with": "persistent memory layer for any framework",
            "status": "documented",
        },
        {
            "name": "mastra",
            "repo": "mastra/mastra",
            "url": "https://github.com/mastra/mastra",
            "stars": "TS-native",
            "why": "TypeScript-native workflows, memory, Studio.",
            "integrates_with": "TS-console agent tooling",
            "status": "documented",
        },
        {
            "name": "dify",
            "repo": "dify-ai/dify",
            "url": "https://github.com/dify-ai/dify",
            "stars": "75K",
            "why": "Visual agent builder + RAG, self-hosted, plugin ecosystem.",
            "integrates_with": "visual builder / RAG frontend",
            "status": "documented",
        },
        {
            "name": "semantic-kernel",
            "repo": "microsoft/semantic-kernel",
            "url": "https://github.com/microsoft/semantic-kernel",
            "stars": "enterprise",
            "why": "Enterprise .NET/Python/Java, skills, planners.",
            "integrates_with": "enterprise skill orchestration",
            "status": "documented",
        },
        {
            "name": "nextjs",
            "repo": "vercel/next.js",
            "url": "https://github.com/vercel/next.js",
            "stars": "120K+",
            "version": "16.3.1 (2026-08-13)",
            "why": "Instant Navigations (SPA-like), faster dev server, better AI tooling, July 2026 security patches (4 HIGH, 5 MEDIUM). Turbopack memory fixes, Node streams by default.",
            "integrates_with": "harness-web (already on 16.3.1, build with --webpack on arm64)",
            "status": "integrated",
        },
    ],
}


def list_repos(tier: str | None = None) -> dict[str, Any]:
    if tier:
        return {tier: REPO_TIERS.get(tier, [])}
    return REPO_TIERS


def summary() -> dict[str, Any]:
    counts = {k: len(v) for k, v in REPO_TIERS.items()}
    return {
        "total": sum(counts.values()),
        "tiers": len(REPO_TIERS),
        "counts": counts,
        "integrated": [r["name"] for r in REPO_TIERS["tier1_xai_native"] if r["status"] == "integrated"]
                    + [r["name"] for r in REPO_TIERS["tier3_specialized"] if r["status"] == "integrated"],
        "latest_updates": [
            "Grok 4.6 (2026-08-12): xhigh reasoning, 500k ctx, prompt_cache_key, Priority Processing",
            "AgentScope 2.0.6 (2026-08-07): MCP/Skill Hubs, Apple Container, Feishu/Discord",
            "crewAI 1.15.16 (2026-08-14): UUID context, telemetry, IBM Db2",
            "Next.js 16.3.1 (2026-08-13): Instant Nav, security patches",
            "LangGraph 1.2.111 (2026-08-11): trace_policy, stream_events v3",
        ],
    }


def list_repos(tier: str | None = None) -> dict[str, Any]:
    if tier:
        return {tier: REPO_TIERS.get(tier, [])}
    return REPO_TIERS


def summary() -> dict[str, Any]:
    counts = {k: len(v) for k, v in REPO_TIERS.items()}
    return {
        "total": sum(counts.values()),
        "tiers": len(REPO_TIERS),
        "counts": counts,
        "integrated": [r["name"] for r in REPO_TIERS["tier1_xai_native"] if r["status"] == "integrated"],
    }
