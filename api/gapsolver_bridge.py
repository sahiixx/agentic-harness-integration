"""GapSolver — Revenue-scored gap discovery bridge."""
from __future__ import annotations

import json
from typing import Any

import api.core as core


async def discover_gaps(
    industry: str,
    location: str = "Dubai",
    top_n: int = 5,
) -> dict[str, Any]:
    """Discover business gaps and score by revenue potential."""
    trace = core.Trace(
        pattern="gapsolver_discover",
        input_payload={"industry": industry, "location": location},
    )

    system_prompt = (
        "You are a market research analyst. Identify gaps in the given industry/location. "
        'Reply as a JSON list: [{"category": "...", "description": "...", '
        '"revenue_score": 0.0-1.0, "urgency": "low|medium|high"}]'
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Industry: {industry}, Location: {location}"},
    ]

    raw = await core.azure_complete(messages, temperature=0.5, max_tokens=1024)
    trace.model_calls = 1
    trace.cost_usd = 0.003

    gaps: list[core.Gap] = []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            for item in parsed:
                gaps.append(
                    core.Gap(
                        category=item.get("category", ""),
                        description=item.get("description", ""),
                        revenue_score=float(item.get("revenue_score", 0.0)),
                        urgency=item.get("urgency", "medium"),
                        source="llm",
                    )
                )
    except Exception as e:
        trace.status = "escalated"
        trace.escalated = True
        trace.output_payload = {"error": str(e), "raw": raw}
        return {"trace": trace.model_dump(), "gaps": [], "error": str(e)}

    gaps.sort(key=lambda g: g.revenue_score, reverse=True)
    top = gaps[:top_n]

    trace.status = "done"
    trace.output_payload = {
        "discovered": len(gaps),
        "returned": len(top),
        "gaps": [g.model_dump() for g in top],
    }

    return {
        "trace": trace.model_dump(),
        "gaps": [g.model_dump() for g in top],
    }
