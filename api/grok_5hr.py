"""5-hour autonomous Grok session — runs grok_chat in a loop for 5h, logs improvements.

Run: python -m api.grok_5hr   (requires XAI_API_KEY in env)
"""
from __future__ import annotations

import asyncio
import time
from datetime import datetime

from api.grok_bridge import grok_chat

DURATION = 5 * 3600  # 5 hours
INTERVAL = 300  # 5 min between turns
LOG = "/tmp/opencode/grok_5hr.log"

SYSTEM = (
    "You are SAHIIX Grok, an autonomous improvement agent for the agentic-harness "
    "integration (FastAPI + Next.js console on a Termux/Android phone). Each turn, "
    "propose ONE concrete, shippable improvement and a one-line code sketch."
)


async def run() -> None:
    start = time.time()
    turn = 0
    with open(LOG, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] 5hr Grok session START\n")
    while time.time() - start < DURATION:
        turn += 1
        messages = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Turn {turn}: propose the next improvement."},
        ]
        try:
            res = await grok_chat(messages)
            content = res.get("content", str(res)) if isinstance(res, dict) else str(res)
            line = f"[{datetime.now().isoformat()}] turn {turn}: {str(content)[:240]}\n"
        except Exception as e:  # noqa: BLE001
            line = f"[{datetime.now().isoformat()}] turn {turn} ERROR: {e}\n"
        with open(LOG, "a") as f:
            f.write(line)
        await asyncio.sleep(INTERVAL)
    with open(LOG, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] 5hr Grok session END ({turn} turns)\n")


if __name__ == "__main__":
    asyncio.run(run())
