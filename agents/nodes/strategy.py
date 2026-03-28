"""Strategy Agent — synthesizes product + brainstorm + research into LaunchStrategy."""

from __future__ import annotations
import json
from state import VibeLaunchState, LaunchStrategy
from nodes.base import llm_json
from tools.ws_notifier import notify


SYSTEM_PROMPT = """You are the Strategy Agent for Vibe Launcher.

Synthesize everything about the product, ICP, and research into a concrete LaunchStrategy.

X Algorithm principles:
- Optimize for reposts (20x), replies (13.5x), bookmarks (10x)
- No hashtags ever
- External links always in first reply
- No "like and RT" CTAs
- Native video 2-4x more reach
- Best days: Tuesday/Wednesday; best times: 9-11 AM or 2-4 PM
- Hook tweet is the most important piece

Be specific to this product and audience — not generic advice.
Return valid JSON matching LaunchStrategy schema."""


async def run_strategy(state: VibeLaunchState) -> dict:
    ws = state["ws_channel"]
    product = state.get("product") or {}
    brainstorm = state.get("brainstorm_responses") or {}
    research = state.get("research_brief") or {}

    todos = [
        {"id": 1, "task": "Craft launch narrative and ICP definition", "status": "in_progress"},
        {"id": 2, "task": "Set posting schedule and visual direction", "status": "pending"},
    ]

    await notify(ws, "stage_update", {
        "name": "strategy", "label": "Strategy", "status": "running", "todos": todos,
    })

    context = f"""Product: {json.dumps(product, indent=2)}
Brainstorm responses: {json.dumps(brainstorm, indent=2)}
Research brief: {json.dumps(research, indent=2)[:3000]}"""

    # Use research brief's content_strategy directly — don't regenerate
    research_content_strategy = research.get("content_strategy", {})

    result = await llm_json(
        system=SYSTEM_PROMPT,
        user=f"""{context}\n\nIMPORTANT: The deep research agent already decided the content formats.
Use EXACTLY these format decisions — do not change or contradict them:
{json.dumps(research_content_strategy, indent=2)}

Return LaunchStrategy JSON:
- narrative (str): core story arc (2-3 sentences)
- icp (str): precise ICP definition
- tone (str): voice direction
- posting_day (str)
- posting_time (str)
- timezone (str)
- visual_brief: {{ "aesthetic": str, "color_palette": [str, 3-5 hex codes], "style": str, "mood": str }}

Do NOT include content_strategy — it will be inherited from research.
""",
    )

    # Inherit content_strategy from research, not strategy LLM
    result["content_strategy"] = research_content_strategy
    strategy = LaunchStrategy(**result).model_dump()

    todos[0]["status"] = "done"
    todos[1]["status"] = "done"
    await notify(ws, "stage_update", {
        "name": "strategy", "label": "Strategy", "status": "done", "todos": todos,
    })

    # Emit visual step outputs
    await notify(ws, "step_output", {
        "stage": "strategy", "step": "narrative",
        "label": "Launch Strategy",
        "data": {"narrative": strategy.get("narrative"), "icp": strategy.get("icp"), "tone": strategy.get("tone")},
    })
    await notify(ws, "step_output", {
        "stage": "strategy", "step": "schedule",
        "label": "Posting Schedule",
        "data": {"day": strategy.get("posting_day"), "time": strategy.get("posting_time"), "timezone": strategy.get("timezone")},
    })
    await notify(ws, "step_output", {
        "stage": "strategy", "step": "format_decisions",
        "label": "Content Formats",
        "data": strategy.get("content_strategy"),
    })
    await notify(ws, "step_output", {
        "stage": "strategy", "step": "visual_brief",
        "label": "Visual Direction",
        "data": strategy.get("visual_brief"),
    })

    return {
        "strategy": strategy,
        "agent_traces": {**(state.get("agent_traces") or {}), "strategy": {"todos": todos}},
    }
