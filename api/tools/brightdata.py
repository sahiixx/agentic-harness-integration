"""Bright Data web scraping / SERP client."""
from __future__ import annotations

import os
from typing import Any, Optional

import httpx

BRIGHTDATA_BASE = "https://api.brightdata.com"


class BrightDataClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("BRIGHTDATA_API_KEY", "")
        self._cost_usd = 0.0

    async def serp(self, query: str, country: str = "us") -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("Bright Data API key missing")

        url = f"{BRIGHTDATA_BASE}/request"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "zone": "serp_zone",
            "url": f"https://www.google.com/search?q={query}&gl={country}",
            "format": "json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            self._cost_usd += 0.05
            return data

    async def scrape(self, target_url: str) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("Bright Data API key missing")

        url = f"{BRIGHTDATA_BASE}/request"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "zone": "scraping_zone",
            "url": target_url,
            "format": "raw",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            self._cost_usd += 0.08
            return data

    @property
    def cost_usd(self) -> float:
        return self._cost_usd
