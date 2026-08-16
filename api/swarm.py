"""Multi-model swarm — run parallel queries across all free providers."""
from __future__ import annotations

import asyncio
from typing import Any

import httpx

from api.grok_bridge import FREE_PROVIDERS, _get_free_provider


async def swarm_chat(messages: list[dict], **kwargs) -> dict[str, Any]:
    """Run same prompt across all available providers in parallel."""
    
    async def query_provider(pname: str) -> dict[str, Any]:
        creds = _get_free_provider(pname)
        if not creds:
            return {"provider": pname, "error": "not configured", "success": False}
        
        base_url, api_key = creds
        provider_model = FREE_PROVIDERS[pname]["models"].get("grok", "grok-4.6")
        headers = {"Content-Type": "application/json"}
        url = f"{base_url}/chat/completions"
        payload = {"model": provider_model, "messages": messages, **kwargs}
        if pname == "azure":
            headers["api-key"] = api_key
            url = f"{base_url}/openai/deployments/{provider_model}/chat/completions?api-version=2024-06-01"
            payload.pop("model", None)
        else:
            headers["Authorization"] = f"Bearer {api_key}"

        async with httpx.AsyncClient(timeout=60.0) as c:
            try:
                r = await c.post(url, headers=headers, json=payload)
                if r.status_code == 200:
                    data = r.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return {
                        "provider": pname,
                        "model": provider_model,
                        "content": content[:500],
                        "tokens": data.get("usage", {}),
                        "success": True,
                    }
                return {"provider": pname, "error": f"HTTP {r.status_code}: {r.text[:200]}", "success": False}
            except Exception as e:
                return {"provider": pname, "error": f"{type(e).__name__}: {e}", "success": False}
    
    # Run all providers in parallel
    results = await asyncio.gather(*[query_provider(p) for p in FREE_PROVIDERS.keys()])
    
    # Rank by success + token efficiency
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    return {
        "swarm_results": results,
        "summary": {
            "total": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "best": successful[0]["provider"] if successful else None,
        },
        "consensus": _consensus(successful) if successful else None,
    }


def _consensus(successful: list[dict]) -> str | None:
    """Simple consensus: most common first sentence."""
    if not successful:
        return None
    first_sentences = []
    for r in successful:
        content = r.get("content", "").strip()
        if content:
            first = content.split(".")[0] + "."
            first_sentences.append(first)
    if not first_sentences:
        return None
    # Return most common
    from collections import Counter
    return Counter(first_sentences).most_common(1)[0][0]