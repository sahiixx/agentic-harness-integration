"""NEXUS Deal Engine — 4-worker lead enrichment bridge."""
from __future__ import annotations

import asyncio
from typing import Any

import api.core as core
from api.tools.apollo import ApolloClient
from api.tools.brightdata import BrightDataClient


async def _worker_apollo(lead: core.Lead) -> dict[str, Any]:
    client = ApolloClient()
    try:
        data = await client.enrich_person(lead.email)
        return {"source": "apollo", "data": data, "cost": client.cost_usd}
    except Exception as e:
        return {"source": "apollo", "error": str(e), "cost": 0.0}


async def _worker_brightdata(lead: core.Lead) -> dict[str, Any]:
    client = BrightDataClient()
    try:
        query = f"{lead.name} {lead.company}"
        data = await client.serp(query)
        return {"source": "brightdata", "data": data, "cost": client.cost_usd}
    except Exception as e:
        return {"source": "brightdata", "error": str(e), "cost": 0.0}


async def _worker_llm_summary(lead: core.Lead, context: str) -> dict[str, Any]:
    prompt = (
        "Summarize lead potential in one sentence. "
        'Reply JSON: {"score": 0-1, "note": "..."}'
    )
    messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": f"Lead: {lead.name} at {lead.company}. Context: {context}",
        },
    ]
    try:
        raw = await core.azure_complete(messages, temperature=0.3, max_tokens=256)
        import json
        parsed = json.loads(raw)
        return {"source": "llm_summary", "data": parsed, "cost": 0.002}
    except Exception as e:
        return {"source": "llm_summary", "error": str(e), "cost": 0.0}


async def _worker_verification(lead: core.Lead) -> dict[str, Any]:
    score = 0
    if "@" in lead.email:
        score += 0.3
    if lead.phone:
        score += 0.3
    if lead.company:
        score += 0.2
    if lead.linkedin:
        score += 0.2
    return {"source": "verification", "data": {"completeness": score}, "cost": 0.0}


async def enrich_lead(lead: core.Lead) -> dict[str, Any]:
    """Run 4 workers in parallel, merge results."""
    trace = core.Trace(pattern="nexus_enrich", input_payload=lead.model_dump())

    apollo_task = asyncio.create_task(_worker_apollo(lead))
    brightdata_task = asyncio.create_task(_worker_brightdata(lead))
    verification_task = asyncio.create_task(_worker_verification(lead))

    apollo_res, brightdata_res, verification_res = await asyncio.gather(
        apollo_task, brightdata_task, verification_task
    )

    context = f"Apollo: {apollo_res.get('data', {})}"
    llm_task = asyncio.create_task(_worker_llm_summary(lead, context))
    llm_res = await llm_task

    total_cost = sum(r.get("cost", 0.0) for r in [apollo_res, brightdata_res, verification_res, llm_res])
    trace.output_payload = {
        "apollo": apollo_res,
        "brightdata": brightdata_res,
        "verification": verification_res,
        "llm_summary": llm_res,
        "total_cost_usd": total_cost,
    }
    trace.status = "done"
    trace.cost_usd = total_cost

    return {
        "trace": trace.model_dump(),
        "lead": lead.model_dump(),
        "enrichment": trace.output_payload,
    }
