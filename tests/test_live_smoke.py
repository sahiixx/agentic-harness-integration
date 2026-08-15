"""Live smoke test — validates real Azure connectivity.

Skipped unless AZURE_FOUNDRY_API_KEY is present.
Run separately: pytest tests/test_live_smoke.py -v
"""
from __future__ import annotations

import os
import pytest

import api.core as core


pytestmark = pytest.mark.skipif(
    not os.getenv("AZURE_FOUNDRY_API_KEY"),
    reason="AZURE_FOUNDRY_API_KEY not set — skipping live test",
)


@pytest.mark.asyncio
async def test_live_azure_complete():
    """Verify Azure AI Foundry responds to a simple completion."""
    messages = [
        {"role": "system", "content": "Reply with only the word OK."},
        {"role": "user", "content": "Say OK."},
    ]
    result = await core.azure_complete(messages, temperature=0.0, max_tokens=10)
    assert isinstance(result, str)
    assert len(result) > 0
    print(f"Live response: {result}")


@pytest.mark.asyncio
async def test_live_azure_embed():
    """Verify Azure embedding endpoint works."""
    texts = ["hello world", "test embedding"]
    embeddings = await core.azure_embed(texts)
    assert len(embeddings) == 2
    assert len(embeddings[0]) > 100  # typical embedding dimension
    print(f"Embedding dims: {len(embeddings[0])}")


@pytest.mark.asyncio
async def test_live_health_via_fastapi():
    """Spin up FastAPI app and hit health endpoint."""
    from fastapi.testclient import TestClient
    from api.main import app

    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "6.0.0"


@pytest.mark.asyncio
async def test_live_gapclaw_hunt():
    """Run a real GapClaw hunt with live Azure calls."""
    from api.gapclaw_bridge import hunt

    result = await hunt("AI automation companies in Dubai", max_model_calls=3)
    assert "trace" in result
    assert result["trace"]["model_calls"] <= 3
    print(f"GapClaw steps: {len(result.get('steps', []))}")
