"""Tool tests — 9 tests total.

v6 fix: Mock (sync) for httpx.Response, AsyncMock only for AsyncClient methods.
This matches httpx's actual API where Response.json() is synchronous.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch, Mock, AsyncMock

from api.tools.apollo import ApolloClient
from api.tools.brightdata import BrightDataClient
from api.tools.wati import WatiClient


# ---------------------------------------------------------------------------
# Apollo
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_apollo_search_people(mock_httpx_client):
    client_mock = mock_httpx_client(response_json={"people": [{"name": "Alice"}]})
    with patch("httpx.AsyncClient", return_value=client_mock):
        apollo = ApolloClient(api_key="test_key")
        result = await apollo.search_people("AI Dubai")
    assert result["people"][0]["name"] == "Alice"
    assert apollo.cost_usd > 0


@pytest.mark.asyncio
async def test_apollo_enrich_person(mock_httpx_client):
    client_mock = mock_httpx_client(response_json={"person": {"name": "Bob"}})
    with patch("httpx.AsyncClient", return_value=client_mock):
        apollo = ApolloClient(api_key="test_key")
        result = await apollo.enrich_person("bob@example.com")
    assert result["person"]["name"] == "Bob"


# ---------------------------------------------------------------------------
# Bright Data
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_brightdata_serp(mock_httpx_client):
    client_mock = mock_httpx_client(response_json={"organic": [{"title": "Result 1"}]})
    with patch("httpx.AsyncClient", return_value=client_mock):
        bd = BrightDataClient(api_key="test_key")
        result = await bd.serp("AI automation")
    assert result["organic"][0]["title"] == "Result 1"
    assert bd.cost_usd > 0


@pytest.mark.asyncio
async def test_brightdata_scrape(mock_httpx_client):
    client_mock = mock_httpx_client(response_json={"html": "<html></html>"})
    with patch("httpx.AsyncClient", return_value=client_mock):
        bd = BrightDataClient(api_key="test_key")
        result = await bd.scrape("https://example.com")
    assert result["html"] == "<html></html>"


# ---------------------------------------------------------------------------
# WATI
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_wati_send_template(mock_httpx_client):
    client_mock = mock_httpx_client(response_json={"status": "sent"})
    with patch("httpx.AsyncClient", return_value=client_mock):
        wati = WatiClient(api_key="test_key")
        result = await wati.send_template("+971501234567", "hello_template")
    assert result["status"] == "sent"
    assert wati.cost_usd > 0


@pytest.mark.asyncio
async def test_wati_send_text(mock_httpx_client):
    client_mock = mock_httpx_client(response_json={"status": "delivered"})
    with patch("httpx.AsyncClient", return_value=client_mock):
        wati = WatiClient(api_key="test_key")
        result = await wati.send_text("+971501234567", "Hello there")
    assert result["status"] == "delivered"


# ---------------------------------------------------------------------------
# Retry logic, failure handling, cost tracking
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tool_retry_logic(mock_httpx_client):
    # First call fails, second succeeds
    fail_resp = Mock()
    fail_resp.status_code = 502
    fail_resp.raise_for_status.side_effect = Exception("Bad Gateway")
    fail_resp.json.return_value = {}

    ok_resp = Mock()
    ok_resp.status_code = 200
    ok_resp.json.return_value = {"people": [{"name": "Retry"}]}
    ok_resp.raise_for_status = Mock()

    client_mock = mock_httpx_client()
    client_mock.post = AsyncMock(side_effect=[fail_resp, ok_resp])

    with patch("httpx.AsyncClient", return_value=client_mock):
        apollo = ApolloClient(api_key="test_key")
        # First attempt fails
        with pytest.raises(Exception):
            await apollo.search_people("test")
        # Second attempt succeeds
        result = await apollo.search_people("test")
    assert result["people"][0]["name"] == "Retry"


@pytest.mark.asyncio
async def test_tool_failure_handling():
    apollo = ApolloClient(api_key="")
    with pytest.raises(RuntimeError, match="missing"):
        await apollo.search_people("test")

    bd = BrightDataClient(api_key="")
    with pytest.raises(RuntimeError, match="missing"):
        await bd.serp("test")

    wati = WatiClient(api_key="")
    with pytest.raises(RuntimeError, match="missing"):
        await wati.send_text("+123", "hi")


@pytest.mark.asyncio
async def test_tool_cost_tracking(mock_httpx_client):
    client_mock = mock_httpx_client(response_json={"people": []})
    with patch("httpx.AsyncClient", return_value=client_mock):
        apollo = ApolloClient(api_key="test_key")
        await apollo.search_people("q1")
        await apollo.enrich_person("a@b.com")
        assert apollo.cost_usd == 0.03  # 0.01 + 0.02

    client_mock2 = mock_httpx_client(response_json={"organic": []})
    with patch("httpx.AsyncClient", return_value=client_mock2):
        bd = BrightDataClient(api_key="test_key")
        await bd.serp("q")
        await bd.scrape("https://x.com")
        assert bd.cost_usd == 0.13  # 0.05 + 0.08

    client_mock3 = mock_httpx_client(response_json={"status": "ok"})
    with patch("httpx.AsyncClient", return_value=client_mock3):
        wati = WatiClient(api_key="test_key")
        await wati.send_template("+1", "t")
        await wati.send_text("+1", "m")
        assert wati.cost_usd == 0.01  # 0.005 + 0.005
