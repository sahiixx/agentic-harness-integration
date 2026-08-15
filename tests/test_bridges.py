"""Bridge tests — 4 tests total."""
from __future__ import annotations

import pytest
from unittest.mock import patch, AsyncMock, Mock

import api.core as core
from api.nexus_bridge import enrich_lead
from api.gapclaw_bridge import hunt
from api.sara_bridge import generate_script
from api.gapsolver_bridge import discover_gaps


# ---------------------------------------------------------------------------
# 1. NEXUS enrichment
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_nexus_enrich(mock_azure_complete):
    mock_azure_complete.return_value = '{"score": 0.85, "note": "strong lead"}'
    lead = core.Lead(name="Alice", email="alice@example.com", company="Acme", phone="+971...")
    result = await enrich_lead(lead)
    assert result["lead"]["email"] == "alice@example.com"
    assert "enrichment" in result
    assert "apollo" in result["enrichment"]
    assert "verification" in result["enrichment"]


# ---------------------------------------------------------------------------
# 2. GapClaw hunt — budget verified (v6 fix: 5-call mock sequence)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gapclaw_hunt_budget_verified(mock_azure_complete):
    mock_azure_complete.side_effect = [
        "Thought: Search Apollo\nAction: apollo_search\nAction Input: {\"query\": \"AI agency\"}",
        "Thought: Search Bright Data\nAction: brightdata_serp\nAction Input: {\"query\": \"AI agency Dubai\"}",
        "Thought: Analyze\nAction: apollo_search\nAction Input: {\"query\": \"startup\"}",
        "Thought: More data\nAction: brightdata_serp\nAction Input: {\"query\": \"funding\"}",
        "Thought: Done\nAction: finish\nAction Input: {\"result\": \"Found 3 leads\"}",
    ]
    result = await hunt("AI agencies in Dubai", max_model_calls=8)
    assert result["trace"]["status"] == "done"
    assert result["result"] == "Found 3 leads"
    assert result["trace"]["model_calls"] <= 8
    assert len(result["steps"]) == 5


# ---------------------------------------------------------------------------
# 3. SARA generate
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sara_generate(mock_azure_complete):
    mock_azure_complete.side_effect = [
        "Draft script one",
        '{"score": 0.88, "feedback": "good hook"}',
    ]
    result = await generate_script(
        topic="AI in real estate",
        rubric={"hook": 1, "clarity": 1},
        max_iterations=3,
    )
    assert result["script"] == "Draft script one"
    assert result["score"] == 0.88
    assert result["iterations"] == 1


# ---------------------------------------------------------------------------
# 4. GapSolver discover
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gapsolver_discover(mock_azure_complete):
    mock_azure_complete.return_value = (
        '[{"category": "automation", "description": "No AI SDR", "revenue_score": 0.92, "urgency": "high"},'
        '{"category": "content", "description": "No video pipeline", "revenue_score": 0.75, "urgency": "medium"}]'
    )
    result = await discover_gaps("real estate", location="Dubai", top_n=3)
    assert len(result["gaps"]) == 2
    assert result["gaps"][0]["revenue_score"] == 0.92
    assert result["trace"]["status"] == "done"
