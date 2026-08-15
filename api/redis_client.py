"""Redis connection with graceful degradation."""
from __future__ import annotations

import os
from typing import Optional

import redis.asyncio as redis

_REDIS: Optional[redis.Redis] = None


async def get_redis() -> Optional[redis.Redis]:
    global _REDIS
    if _REDIS is not None:
        return _REDIS
    url = os.getenv("REDIS_URL", "")
    if not url:
        return None
    try:
        _REDIS = redis.from_url(url, decode_responses=True)
        await _REDIS.ping()
        return _REDIS
    except Exception:
        return None


async def get_cache(key: str) -> Optional[str]:
    r = await get_redis()
    if r is None:
        return None
    return await r.get(key)


async def set_cache(key: str, value: str, ttl: int = 300):
    r = await get_redis()
    if r is None:
        return None
    return await r.setex(key, ttl, value)
