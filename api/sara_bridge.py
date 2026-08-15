"""SARA — Evaluator-Optimizer + Reflection for video script generation."""
from __future__ import annotations

import json
from typing import Any

import api.core as core


async def generate_script(
    topic: str,
    rubric: dict[str, Any],
    max_iterations: int = 3,
) -> dict[str, Any]:
    """Rubric-gated generation with eval-optimize loop."""
    trace = core.Trace(pattern="sara_generate", input_payload={"topic": topic, "rubric": rubric})
    model_calls = 0
    total_cost = 0.0

    draft = ""
    for iteration in range(1, max_iterations + 1):
        gen_messages = [
            {
                "role": "system",
                "content": "You are a video script writer. Write a 60-second script.",
            },
            {"role": "user", "content": f"Topic: {topic}. Previous feedback: {trace.output_payload.get('feedback', 'none')}"},
        ]
        draft = await core.azure_complete(gen_messages, temperature=0.7, max_tokens=512)
        model_calls += 1
        total_cost += 0.002

        eval_prompt = (
            f"Score this script against rubric: {json.dumps(rubric)}. "
            'Reply JSON: {"score": 0-1, "feedback": "..."}'
        )
        eval_messages = [
            {"role": "system", "content": eval_prompt},
            {"role": "user", "content": draft},
        ]
        eval_raw = await core.azure_complete(
            eval_messages,
            model=__import__("os").getenv("AZURE_JUDGE_MODEL", "claude-opus-5"),
            temperature=0.2,
            max_tokens=256,
        )
        model_calls += 1
        total_cost += 0.005

        try:
            eval_result = json.loads(eval_raw)
        except Exception:
            eval_result = {"score": 0.0, "feedback": "Parse error"}

        trace.output_payload = {
            "iteration": iteration,
            "draft": draft,
            "score": eval_result.get("score", 0.0),
            "feedback": eval_result.get("feedback", ""),
        }

        if eval_result.get("score", 0.0) >= 0.85:
            trace.status = "done"
            trace.model_calls = model_calls
            trace.cost_usd = total_cost
            return {
                "trace": trace.model_dump(),
                "script": draft,
                "score": eval_result.get("score", 0.0),
                "iterations": iteration,
            }

    trace.status = "done"
    trace.model_calls = model_calls
    trace.cost_usd = total_cost
    return {
        "trace": trace.model_dump(),
        "script": draft,
        "score": trace.output_payload.get("score", 0.0),
        "iterations": max_iterations,
    }
