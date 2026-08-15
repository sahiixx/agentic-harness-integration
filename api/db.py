"""PostgreSQL connection with graceful degradation."""
from __future__ import annotations

import os
from typing import Optional

import asyncpg

_POOL: Optional[asyncpg.Pool] = None


async def get_pool() -> Optional[asyncpg.Pool]:
    global _POOL
    if _POOL is not None:
        return _POOL
    dsn = os.getenv("DATABASE_URL", "")
    if not dsn:
        return None
    try:
        _POOL = await asyncpg.create_pool(dsn, min_size=1, max_size=10)
        return _POOL
    except Exception:
        return None


async def fetch(query: str, *args):
    pool = await get_pool()
    if pool is None:
        return []
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)


async def execute(query: str, *args):
    pool = await get_pool()
    if pool is None:
        return None
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)
