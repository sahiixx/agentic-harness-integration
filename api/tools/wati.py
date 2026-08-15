"""WATI WhatsApp Business API client."""
from __future__ import annotations

import os
from typing import Any, Optional

import httpx

WATI_BASE = "https://app-server.wati.io"


class WatiClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("WATI_API_KEY", "")
        self._cost_usd = 0.0

    async def send_template(
        self,
        phone: str,
        template_name: str,
        language_code: str = "en",
        params: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("WATI API key missing")

        url = f"{WATI_BASE}/api/v1/sendTemplateMessage"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "template_name": template_name,
            "broadcast_name": template_name,
            "parameters": params or [],
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url, headers=headers, json=payload, params={"whatsappNumber": phone}
            )
            resp.raise_for_status()
            data = resp.json()
            self._cost_usd += 0.005
            return data

    async def send_text(self, phone: str, message: str) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("WATI API key missing")

        url = f"{WATI_BASE}/api/v1/sendSessionMessage"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "text/plain",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url,
                headers=headers,
                content=message,
                params={"whatsappNumber": phone},
            )
            resp.raise_for_status()
            data = resp.json()
            self._cost_usd += 0.005
            return data

    @property
    def cost_usd(self) -> float:
        return self._cost_usd
