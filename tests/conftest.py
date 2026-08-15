"""Test configuration — safety net blocks real HTTP."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, Mock


# ---------------------------------------------------------------------------
# Safety net: block any unmocked httpx call
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True, scope="session")
def _block_real_network():
    import httpx
    original_post = httpx.AsyncClient.post
    original_get = httpx.AsyncClient.get
    original_request = httpx.AsyncClient.request

    def _block_post(*args, **kwargs):
        raise RuntimeError("REAL NETWORK CALL BLOCKED")

    def _block_get(*args, **kwargs):
        raise RuntimeError("REAL NETWORK CALL BLOCKED")

    def _block_request(*args, **kwargs):
        raise RuntimeError("REAL NETWORK CALL BLOCKED")

    httpx.AsyncClient.post = _block_post
    httpx.AsyncClient.get = _block_get
    httpx.AsyncClient.request = _block_request

    yield

    httpx.AsyncClient.post = original_post
    httpx.AsyncClient.get = original_get
    httpx.AsyncClient.request = original_request


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_azure_complete():
    """Patch api.core.azure_complete for the duration of a test.

    All modules use `import api.core as core` + `core.azure_complete()`.
    Patching `api.core.azure_complete` propagates everywhere.
    """
    from unittest.mock import patch
    with patch("api.core.azure_complete") as m:
        yield m


@pytest.fixture
def mock_httpx_response():
    """Return a sync Mock response (json() is sync per httpx API)."""
    def _make(json_data=None, status_code=200, text=""):
        resp = Mock()
        resp.status_code = status_code
        resp.json.return_value = json_data or {}
        resp.text = text
        resp.raise_for_status = Mock()
        return resp
    return _make


@pytest.fixture
def mock_httpx_client(mock_httpx_response):
    """Return an AsyncMock client whose .post()/.get() return sync Mock responses."""
    from unittest.mock import AsyncMock, patch

    def _make(response_json=None, status_code=200):
        resp = mock_httpx_response(json_data=response_json, status_code=status_code)
        client = AsyncMock()
        client.post = AsyncMock(return_value=resp)
        client.get = AsyncMock(return_value=resp)
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)
        return client
    return _make
