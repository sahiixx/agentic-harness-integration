"""Pattern endpoint tests — 18 tests total."""
from __future__ import annotations

import json
import pytest
from unittest.mock import patch, AsyncMock, Mock
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Prompt Chaining
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_chain_basic(mock_azure_complete):
    mock_azure_complete.side_effect = ["step1", "step2", "step3"]
    resp = client.post("/pattern/chain", json={"prompts": ["a", "b", "c"], "temperature": 0.5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"] == ["step1", "step2", "step3"]
    assert data["trace"]["model_calls"] == 3


@pytest.mark.asyncio
async def test_chain_empty_prompts(mock_azure_complete):
    resp = client.post("/pattern/chain", json={"prompts": [], "temperature": 0.5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"] == []
    assert data["trace"]["model_calls"] == 0


# ---------------------------------------------------------------------------
# 2. Routing
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_route_basic(mock_azure_complete):
    mock_azure_complete.side_effect = ["sales", "Sales reply"]
    resp = client.post("/pattern/route", json={
        "input_text": "I want to buy",
        "routes": {"sales": "You are a sales rep.", "support": "You are support."},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["selected_route"] == "sales"
    assert data["output"] == "Sales reply"


@pytest.mark.asyncio
async def test_route_unknown_fallback(mock_azure_complete):
    mock_azure_complete.side_effect = ["unknown_route", "Fallback reply"]
    resp = client.post("/pattern/route", json={
        "input_text": "hello",
        "routes": {"sales": "Sales", "support": "Support"},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["selected_route"] == "sales"  # fallback to first


# ---------------------------------------------------------------------------
# 3. Parallelization
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_parallel_basic(mock_azure_complete):
    mock_azure_complete.side_effect = ["r1", "r2", "r3"]
    resp = client.post("/pattern/parallel", json={"tasks": ["t1", "t2", "t3"], "temperature": 0.5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"] == ["r1", "r2", "r3"]
    assert data["trace"]["model_calls"] == 3


@pytest.mark.asyncio
async def test_parallel_empty(mock_azure_complete):
    resp = client.post("/pattern/parallel", json={"tasks": [], "temperature": 0.5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"] == []


# ---------------------------------------------------------------------------
# 4. Orchestrator-Workers
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_orchestrate_basic(mock_azure_complete):
    mock_azure_complete.side_effect = [
        '["research", "write"]',   # plan
        "research result",          # worker 1
        "write result",             # worker 2
        "final synthesis",          # synthesize
    ]
    resp = client.post("/pattern/orchestrate", json={"objective": "Create a blog post", "pre_analyze": False})
    assert resp.status_code == 200
    data = resp.json()
    assert data["subtasks"] == ["research", "write"]
    assert data["final"] == "final synthesis"
    assert data["trace"]["model_calls"] == 4


@pytest.mark.asyncio
async def test_orchestrate_with_pre_analyze(mock_azure_complete):
    mock_azure_complete.side_effect = [
        '[{"category": "ai", "description": "gap", "revenue_score": 0.9, "urgency": "high"}]',  # pre-analyze
        '["task1"]',  # plan
        "worker result",  # worker
        "final",  # synthesize
    ]
    resp = client.post("/pattern/orchestrate", json={"objective": "AI agency", "pre_analyze": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["subtasks"] == ["task1"]


# ---------------------------------------------------------------------------
# 5. Evaluator-Optimizer
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_evaluate_optimize_converges(mock_azure_complete):
    mock_azure_complete.side_effect = [
        "draft1",
        '{"score": 0.9, "feedback": "good"}',
    ]
    resp = client.post("/pattern/evaluate_optimize", json={
        "prompt": "Write a headline",
        "rubric": {"clarity": 1},
        "max_iterations": 3,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] == 0.9
    assert data["iterations"] == 1


@pytest.mark.asyncio
async def test_evaluate_optimize_max_iter(mock_azure_complete):
    mock_azure_complete.side_effect = [
        "draft1", '{"score": 0.5, "feedback": "bad"}',
        "draft2", '{"score": 0.6, "feedback": "ok"}',
        "draft3", '{"score": 0.7, "feedback": "better"}',
    ]
    resp = client.post("/pattern/evaluate_optimize", json={
        "prompt": "Write a tagline",
        "rubric": {"catchy": 1},
        "max_iterations": 3,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["iterations"] == 3


# ---------------------------------------------------------------------------
# 6. ReAct
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_react_basic(mock_azure_complete):
    mock_azure_complete.side_effect = [
        "Thought: Search\nAction: apollo_search\nAction Input: {\"query\": \"AI Dubai\"}",
        "Thought: Done\nAction: finish\nAction Input: {}",
    ]
    resp = client.post("/pattern/react", json={"query": "AI companies in Dubai", "max_model_calls": 8})
    assert resp.status_code == 200
    data = resp.json()
    assert data["trace"]["status"] == "done"
    assert len(data["steps"]) >= 1


# ---------------------------------------------------------------------------
# 7. Reflection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reflect_basic(mock_azure_complete):
    mock_azure_complete.side_effect = [
        '{"issues": ["too long"], "score": 0.6}',
        "Rewritten draft here",
    ]
    resp = client.post("/pattern/reflect", json={
        "draft": "Original draft",
        "criteria": ["concise", "clear"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["critique"]["score"] == 0.6
    assert data["rewritten"] == "Rewritten draft here"




# ---------------------------------------------------------------------------
# 8. SSE Streaming
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sse_stream_trace(mock_azure_complete):
    resp = client.get("/stream/trace/t_12345")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "text/event-stream; charset=utf-8"
    body = resp.text
    assert "data:" in body
    assert "pending" in body or "running" in body or "done" in body
    assert "trace_id" in body

# ---------------------------------------------------------------------------
# 9. Subtask parser (4 cases)
# ---------------------------------------------------------------------------

from api.core import _parse_subtasks


def test_subtask_parser_json_list():
    raw = '["a", "b", "c"]'
    assert _parse_subtasks(raw) == ["a", "b", "c"]


def test_subtask_parser_json_object():
    raw = '{"subtasks": ["x", "y"]}'
    assert _parse_subtasks(raw) == ["x", "y"]


def test_subtask_parser_plain_text():
    raw = "task one\ntask two\n\ntask three"
    assert _parse_subtasks(raw) == ["task one", "task two", "task three"]


def test_subtask_parser_empty_input():
    assert _parse_subtasks("") == [""]
    assert _parse_subtasks("   ") == [""]


# ---------------------------------------------------------------------------
# 10. API endpoints + health + safety net
# ---------------------------------------------------------------------------

def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["version"] == "6.0.0"


def test_root_endpoint():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["version"] == "6.0.0"
    assert "v6" in resp.json()["name"]


@pytest.mark.asyncio
async def test_safety_net_blocks_unmocked_http():
    import httpx
    with pytest.raises(RuntimeError, match="REAL NETWORK CALL BLOCKED"):
        async with httpx.AsyncClient() as c:
            await c.get("https://example.com")

# ---------------------------------------------------------------------------
# 11. Auth & Rate Limiting
# ---------------------------------------------------------------------------

def test_auth_disabled_by_default(mock_azure_complete):
    """When JWT_SECRET is not set, auth is disabled — POST works without token."""
    mock_azure_complete.return_value = "ok"
    resp = client.post("/pattern/chain", json={"prompts": ["hi"], "temperature": 0.5})
    assert resp.status_code == 200


def test_auth_token_endpoint_no_secret():
    """Token generation fails when JWT_SECRET is not set."""
    resp = client.post("/auth/token", json={"subject": "test", "expires_minutes": 60})
    assert resp.status_code == 503


def test_cors_headers_present(mock_azure_complete):
    """CORS middleware adds appropriate headers."""
    mock_azure_complete.return_value = "ok"
    resp = client.options("/pattern/chain", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
    })
    assert resp.status_code == 200
    assert "access-control-allow-origin" in resp.headers
