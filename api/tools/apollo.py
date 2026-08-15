"""Apollo.io B2B lead discovery client."""
from __future__ import annotations

import os
from typing import Any, Optional

import httpx

APOLLO_BASE = "https://api.apollo.io/v1"


class ApolloClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("APOLLO_API_KEY", "")
        self._cost_usd = 0.0

    async def search_people(
        self,
        q_keywords: str,
        person_titles: Optional[list[str]] = None,
        page: int = 1,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("Apollo API key missing")

        url = f"{APOLLO_BASE}/mixed_people/search"
        headers = {"Content-Type": "application/json", "Cache-Control": "no-cache"}
        payload = {
            "api_key": self.api_key,
            "q_keywords": q_keywords,
            "page": page,
        }
        if person_titles:
            payload["person_titles"] = person_titles

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            self._cost_usd += 0.01  # rough per-call estimate
            return data

    async def enrich_person(self, email: str) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("Apollo API key missing")

        url = f"{APOLLO_BASE}/people/match"
        headers = {"Content-Type": "application/json", "Cache-Control": "no-cache"}
        payload = {"api_key": self.api_key, "email": email}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            self._cost_usd += 0.02
            return data

    @property
    def cost_usd(self) -> float:
        return self._cost_usd
