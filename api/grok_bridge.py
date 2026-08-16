"""Grok (xAI) bridge — chat, vision, voice.

Uses the native xAI SDK (xai_sdk) when installed, falling back to the
OpenAI-compatible HTTP API. Default model is grok-4.6 (xAI's current flagship).

Grok 4.6 features (Aug 12, 2026):
- 500k context window, text+image input, text output
- reasoning_effort: low / medium / high (default) / xhigh (NEW)
- Prompt caching via `prompt_cache_key` or `x-grok-conv-id` header
- Priority Processing via `service_tier: "priority"` (2x price, faster)
- Knowledge cutoff: Feb 1, 2026
- Native tools: web_search, x_search, code_execution
"""
from __future__ import annotations

import os
import base64
import httpx
from typing import Any

XAI_API_BASE = os.getenv("XAI_API_BASE", "https://api.x.ai/v1")
XAI_API_KEY = os.getenv("XAI_API_KEY")
DEFAULT_MODEL = os.getenv("GROK_MODEL", "grok-4.6")

try:
    from xai_sdk import AsyncClient
    from xai_sdk.chat import user as xai_user, system as xai_system
    from xai_sdk.tools import web_search, x_search, code_execution
    _HAS_SDK = True
except Exception:
    _HAS_SDK = False


def _stub(model: str, content: str = "[stub] Grok response (set XAI_API_KEY for live)") -> dict[str, Any]:
    return {
        "status": "stub",
        "error": "XAI_API_KEY not set" if not XAI_API_KEY else "xai_sdk unavailable",
        "model": model,
        "choices": [{"message": {"role": "assistant", "content": content}}],
    }


async def grok_chat(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    tools: bool = True,
    reasoning_effort: str = "high",  # low | medium | high | xhigh (NEW in 4.6)
    prompt_cache_key: str | None = None,  # for 500k context agent loops
    priority: bool = False,  # Priority Processing (service_tier)
) -> dict[str, Any]:
    """Grok chat with native tool-calling + 4.6 features."""
    if not XAI_API_KEY:
        return _stub(model)
    if _HAS_SDK:
        client = AsyncClient()
        chat = client.chat.create(
            model=model,
            tools=[web_search(), x_search(), code_execution()] if tools else [],
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort,  # NEW: xhigh supported
        )
        if prompt_cache_key:
            chat.set_prompt_cache_key(prompt_cache_key)
        for m in messages:
            role = m.get("role")
            text = m.get("content", "")
            if isinstance(text, list):
                text = " ".join(p.get("text", "") for p in text if isinstance(p, dict))
            chat.append(xai_system(text) if role == "system" else xai_user(text))
        resp = await chat.sample()
        return {
            "status": "ok",
            "model": model,
            "content": resp.content,
            "citations": getattr(resp, "citations", None),
            "usage": getattr(resp, "usage", None),
        }
    # Fallback: OpenAI-compatible with 4.6 headers
    headers = {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json",
    }
    if prompt_cache_key:
        headers["x-grok-conv-id"] = prompt_cache_key  # cache key for agent loops
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "reasoning_effort": reasoning_effort,  # NEW in 4.6
    }
    if priority:
        payload["service_tier"] = "priority"  # Priority Processing (2x price)
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(f"{XAI_API_BASE}/chat/completions", headers=headers, json=payload)
        r.raise_for_status()
        return r.json()


async def grok_vision(
    messages: list[dict],
    image_url: str,
    model: str = "grok-4.6",
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> dict[str, Any]:
    """Grok vision — analyze an image. Appends image_url to last user message."""
    if messages and messages[-1]["role"] == "user":
        content = messages[-1]["content"]
        if isinstance(content, str):
            messages[-1]["content"] = [
                {"type": "text", "text": content},
                {"type": "image_url", "image_url": {"url": image_url}},
            ]
        elif isinstance(content, list):
            content.append({"type": "image_url", "image_url": {"url": image_url}})
    if not XAI_API_KEY:
        return _stub(model, "[stub] vision response")
    headers = {"Authorization": f"Bearer {XAI_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(f"{XAI_API_BASE}/chat/completions", headers=headers, json=payload)
        r.raise_for_status()
        return r.json()


async def grok_voice_transcribe(audio_b64: str, model: str = "grok-2-voice") -> dict[str, Any]:
    """Grok voice — transcribe base64 audio (OpenAI-compatible)."""
    if not XAI_API_KEY:
        return {"status": "stub", "error": "XAI_API_KEY not set", "text": "[stub] transcription"}
    headers = {"Authorization": f"Bearer {XAI_API_KEY}"}
    files = {"file": ("audio.wav", base64.b64decode(audio_b64), "audio/wav")}
    data = {"model": model}
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(f"{XAI_API_BASE}/audio/transcriptions", headers=headers, files=files, data=data)
        r.raise_for_status()
        return r.json()


async def grok_voice_speak(text: str, voice: str = "alloy", model: str = "grok-2-voice") -> bytes:
    """Grok TTS — return audio bytes (OpenAI-compatible)."""
    if not XAI_API_KEY:
        return b"[stub audio]"
    headers = {"Authorization": f"Bearer {XAI_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": model, "input": text, "voice": voice}
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(f"{XAI_API_BASE}/audio/speech", headers=headers, json=payload)
        r.raise_for_status()
        return r.content


def _encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


async def grok_vision_file(messages: list[dict], image_path: str, model: str = "grok-4.6", temperature: float = 0.7, max_tokens: int = 2048) -> dict[str, Any]:
    """Grok vision with local file — uploads as data URI."""
    b64 = _encode_image(image_path)
    data_uri = f"data:image/jpeg;base64,{b64}"
    return await grok_vision(messages, data_uri, model, temperature, max_tokens)


# ─── Grok Bot integration (durable AI teammates) ───
async def grok_bot_delegate(task: str, context: dict | None = None) -> dict[str, Any]:
    """
    Delegate to Grok Bot (durable cloud agents).
    Requires separate Grok Bot API access (x.ai/build).
    """
    if not XAI_API_KEY:
        return _stub("grok-bot", "[stub] Grok Bot delegation - needs Bot API access")
    # Placeholder for future Bot API integration
    return {
        "status": "pending",
        "message": "Grok Bot API not yet public. Use x.ai/build for access.",
        "task": task,
        "context": context,
    }


# ─── Free Provider Bridge (auto-fallback when XAI_API_KEY not set) ───
# FreeTheAi: https://api.freetheai.xyz/v1  (Discord /signup for key)
# token-free-gateway: run locally, 13 providers including Grok
# Puter: https://api.puter.com/puterai/openai/v1/  (Puter auth token)
# Perplexity-API: run locally, Grok 4.1 + others

FREE_PROVIDERS = {
    "azure": {
        "base_url": "https://ij.services.ai.azure.com",
        "key_env": "AZURE_OPENAI_KEY",
        "models": {"grok": "grok-4.3", "chat": "Kimi-K2.6"},
    },
    "freetheai": {
        "base_url": "https://api.freetheai.xyz/v1",
        "key_env": "FREETHEAI_API_KEY",
        "models": {"grok": "xai/grok-4", "chat": "bbl/gpt-4o-mini"},
    },
    "puter": {
        "base_url": "https://api.puter.com/puterai/openai/v1/",
        "key_env": "PUTER_AUTH_TOKEN",
        "models": {"grok": "grok", "chat": "gpt-4o-mini"},
    },
    "ollama": {
        "base_url": "http://127.0.0.1:11434/v1",
        "key_env": "",  # No key needed for local Ollama
        "models": {"grok": "nemotron-3-super:cloud", "chat": "llama3.2:3b"},
    },
}


def _get_free_provider(name: str = "freetheai") -> tuple[str, str] | None:
    """Return (base_url, api_key) for a free provider if configured."""
    cfg = FREE_PROVIDERS.get(name)
    if not cfg:
        return None
    key = os.getenv(cfg["key_env"]) if cfg["key_env"] else "ollama-local"
    if not key:
        return None
    return cfg["base_url"], key


async def grok_chat_free(
    messages: list[dict],
    model: str = "grok-4.6",
    provider: str = "freetheai",
    **kwargs,
) -> dict[str, Any]:
    """
    Grok chat via free OpenAI-compatible providers.
    Falls back through: ollama (local) → freetheai → puter → stub.
    Returns provider error details on failure.
    """
    last_error = None
    # Try azure (real Grok 4.3) first, then ollama (local, no key), then cloud free providers
    for pname in ("azure", "ollama", "freetheai", "puter"):
        creds = _get_free_provider(pname)
        if creds:
            base_url, api_key = creds
            provider_model = FREE_PROVIDERS[pname]["models"].get("grok", model)
            headers = {"Content-Type": "application/json"}
            url = f"{base_url}/chat/completions"
            payload = {"model": provider_model, "messages": messages, **kwargs}
            if pname == "azure":
                headers["api-key"] = api_key
                deployment = provider_model
                url = f"{base_url}/openai/deployments/{deployment}/chat/completions?api-version=2024-06-01"
                payload.pop("model", None)
            else:
                headers["Authorization"] = f"Bearer {api_key}"
            async with httpx.AsyncClient(timeout=60.0) as c:
                try:
                    r = await c.post(url, headers=headers, json=payload)
                    if r.status_code == 200:
                        return r.json()
                    last_error = f"{pname}: HTTP {r.status_code} - {r.text[:200]}"
                except Exception as e:
                    last_error = f"{pname}: {type(e).__name__}: {e}"
    return _stub(model, f"[stub] Free provider error: {last_error or 'no provider configured'}")


async def grok_vision_free(
    messages: list[dict],
    image_url: str,
    provider: str = "freetheai",
    **kwargs,
) -> dict[str, Any]:
    """Grok vision via free providers."""
    if messages and messages[-1]["role"] == "user":
        content = messages[-1]["content"]
        if isinstance(content, str):
            messages[-1]["content"] = [
                {"type": "text", "text": content},
                {"type": "image_url", "image_url": {"url": image_url}},
            ]
    return await grok_chat_free(messages, provider=provider, **kwargs)
