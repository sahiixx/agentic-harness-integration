"""GapClaw — ReAct agent with real tools + deterministic budget."""
from __future__ import annotations

import json
from typing import Any

import api.core as core
from api.tools.apollo import ApolloClient
from api.tools.brightdata import BrightDataClient


MAX_MODEL_CALLS = 8


async def hunt(query: str, max_model_calls: int = MAX_MODEL_CALLS) -> dict[str, Any]:
    """Autonomous ReAct loop with hard call budget."""
    trace = core.Trace(pattern="gapclaw_hunt", input_payload={"query": query})
    steps: list[core.ReActStep] = []
    model_calls = 0
    total_cost = 0.0

    apollo = ApolloClient()
    brightdata = BrightDataClient()

    system_msg = (
        "You are a business research agent. Use tools: apollo_search, brightdata_serp. "
        "Reply in strict ReAct format: Thought: ...\nAction: tool_name\nAction Input: {\"key\": \"value\"}"
    )

    conversation = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": f"Research: {query}"},
    ]

    while model_calls < max_model_calls:
        model_calls += 1
        try:
            raw = await core.azure_complete(conversation, temperature=0.4, max_tokens=512)
            total_cost += 0.002
        except Exception as e:
            trace.status = "escalated"
            trace.escalated = True
            trace.output_payload = {"error": str(e), "steps": [s.model_dump() for s in steps]}
            trace.model_calls = model_calls
            trace.cost_usd = total_cost
            return {"trace": trace.model_dump(), "result": None, "steps": [s.model_dump() for s in steps]}

        step = _parse_react(raw)
        steps.append(step)

        if step.action.lower() in ("finish", "done", "complete"):
            trace.status = "done"
            result_text = step.observation or step.action_input.get("result", "")
            trace.output_payload = {"result": result_text, "steps": [s.model_dump() for s in steps]}
            trace.model_calls = model_calls
            trace.cost_usd = total_cost + apollo.cost_usd + brightdata.cost_usd
            return {
                "trace": trace.model_dump(),
                "result": result_text,
                "steps": [s.model_dump() for s in steps],
            }

        observation = await _run_tool(step.action, step.action_input, apollo, brightdata)
        step.observation = observation
        total_cost += apollo.cost_usd + brightdata.cost_usd

        conversation.append({"role": "assistant", "content": raw})
        conversation.append({"role": "user", "content": f"Observation: {observation}"})

    trace.status = "escalated"
    trace.escalated = True
    trace.output_payload = {
        "error": "max_model_calls exhausted",
        "steps": [s.model_dump() for s in steps],
    }
    trace.model_calls = model_calls
    trace.cost_usd = total_cost
    return {
        "trace": trace.model_dump(),
        "result": None,
        "steps": [s.model_dump() for s in steps],
    }


def _parse_react(raw: str) -> core.ReActStep:
    thought = ""
    action = ""
    action_input: dict[str, Any] = {}

    lines = raw.strip().splitlines()
    for line in lines:
        if line.lower().startswith("thought:"):
            thought = line.split(":", 1)[1].strip()
        elif line.lower().startswith("action:"):
            action = line.split(":", 1)[1].strip()
        elif line.lower().startswith("action input:"):
            try:
                action_input = json.loads(line.split(":", 1)[1].strip())
            except Exception:
                action_input = {"raw": line.split(":", 1)[1].strip()}

    return core.ReActStep(thought=thought, action=action, action_input=action_input)


async def _run_tool(
    action: str, inputs: dict[str, Any], apollo: ApolloClient, brightdata: BrightDataClient
) -> str:
    action = action.lower().replace(" ", "_")
    try:
        if "apollo" in action:
            q = inputs.get("query", "")
            data = await apollo.search_people(q)
            return json.dumps({"results": len(data.get("people", []))})
        elif "brightdata" in action or "serp" in action:
            q = inputs.get("query", "")
            data = await brightdata.serp(q)
            return json.dumps({"results": len(data.get("organic", []))})
        else:
            return f"Unknown tool: {action}"
    except Exception as e:
        return f"Tool error: {e}"
