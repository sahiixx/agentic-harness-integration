"""Azure OpenAI bridge — chat, embeddings via Azure OpenAI endpoint."""
from __future__ import annotations

import os
import httpx
from typing import Any

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://ij.services.ai.azure.com")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "grok-4.3")


def _stub(model: str, content: str = "[stub] Azure OpenAI response (set AZURE_OPENAI_KEY for live)") -> dict[str, Any]:
    return {
        "status": "stub",
        "error": "AZURE_OPENAI_KEY not set" if not AZURE_OPENAI_KEY else "request failed",
        "model": model,
        "choices": [{"message": {"role": "assistant", "content": content}}],
    }


async def azure_chat(
    messages: list[dict],
    model: str = AZURE_OPENAI_DEPLOYMENT,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    **kwargs,
) -> dict[str, Any]:
    """Azure OpenAI chat completion."""
    if not AZURE_OPENAI_KEY:
        return _stub(model)

    url = f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/deployments/{model}/chat/completions"
    params = {"api-version": AZURE_OPENAI_API_VERSION}
    headers = {
        "api-key": AZURE_OPENAI_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        **kwargs,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, params=params, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()


async def azure_embeddings(
    input_text: str | list[str],
    model: str = "text-embedding-3-large",
    **kwargs,
) -> dict[str, Any]:
    """Azure OpenAI embeddings."""
    if not AZURE_OPENAI_KEY:
        return {"status": "stub", "error": "AZURE_OPENAI_KEY not set", "data": []}

    url = f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/deployments/{model}/embeddings"
    params = {"api-version": AZURE_OPENAI_API_VERSION}
    headers = {
        "api-key": AZURE_OPENAI_KEY,
        "Content-Type": "application/json",
    }
    payload = {"input": input_text, **kwargs}

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, params=params, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()


async def azure_chat_stream(
    messages: list[dict],
    model: str = AZURE_OPENAI_DEPLOYMENT,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    **kwargs,
):
    """Azure OpenAI streaming chat."""
    if not AZURE_OPENAI_KEY:
        yield _stub(AZURE_OPENAI_DEPLOYMENT, "[stub] Azure OpenAI streaming")
        return

    url = f"{AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/deployments/{model}/chat/completions"
    params = {"api-version": AZURE_OPENAI_API_VERSION}
    headers = {
        "api-key": AZURE_OPENAI_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
        **kwargs,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, params=params, headers=headers, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    yield data