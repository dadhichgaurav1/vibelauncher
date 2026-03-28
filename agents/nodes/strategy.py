"""
Strategy Agent.
Synthesizes product brief + brainstorm + research into a LaunchStrategy.
"""

from __future__ import annotations
import json
from state import VibeLaunchState, LaunchStrategy
from nodes.base import llm_json, plan_todos
from tools.ws_notifier import notify


SYSTEM_PROMPT = """You are the Strategy Agent for Vibe Launcher.

Your role: synthesize everything we know about the product, the user's ICP definition,
and the deep research into a concrete LaunchStrategy.

X Algorithm principles you must apply:
- Optimize for reposts (20x), replies (13.5x), bookmarks (10x) — in that priority
- No hashtags ever
- External links always go in first reply, never in main post body
- No "like and RT" style CTAs — triggers spam filters
- Native video 2-4x more reach; use if product has demo value
- Best days: Tuesday/Wednesday; best times: 9-11 AM or 2-4 PM in audience timezone
- For tech/builder audience: evenings and weekends are also viable
- Hook tweet: most important piece — spend 50% of writing effort here

Your strategy must be specific to this product and audience — not generic advice.
The narrative, tone, and visual brief should all be tailored to the research.

Return valid JSON matching LaunchStrategy schema."""


async def run_strategy(state: VibeLaunchState) -> dict:
    ws = state["ws_channel"]
    product = state.get("product", {})
    brainstorm = state.get("brainstorm_responses", {})
    research = state.get("research_brief", {})

    await notify(ws, "stage_update", {
        "name": "strategy",
        "label": "Strategy",
        "status": "running",
        "todos": [],
    })

    context = f"""Product: {json.dumps(product, indent=2)}
Brainstorm responses: {json.dumps(brainstorm, indent=2)}
Research brief: {json.dumps(research, indent=2)[:3000]}"""

    # Plan
    todos = await plan_todos(
        "strategy",
        "Define launch strategy: narrative arc, ICP, tone, posting schedule, visual direction",
        context[:1500],
    )

    await notify(ws, "stage_update", {
        "name": "strategy",
        "label": "Strategy",
        "status": "running",
        "todos": todos,
    })

    for todo in todos:
        todo["status"] = "in_progress"
    await notify(ws, "stage_update", {"name": "strategy", "label": "Strategy", "status": "running", "todos": todos})
    for todo in todos:
        todo["status"] = "done"

    # Execute
    result = await llm_json(
        system=SYSTEM_PROMPT,
        user=f"""{context}

Return LaunchStrategy JSON:
- narrative (str): the core story arc of this launch (2-3 sentences)
- icp (str): precise ICP definition based on research
- tone (str): voice and tone direction (e.g. "Sharp and technical, builder-to-builder, no marketing speak")
- posting_day (str)
- posting_time (str)
- timezone (str)
- content_strategy: {{ "formats": [str], "rationale": {{ "tweet": str|null, "thread": str|null, "image": str|null, "video": str|null }} }}
- visual_brief: {{ "aesthetic": str, "color_palette": [str, 3-5 hex codes], "style": str, "mood": str }}
""",
    )

    strategy = LaunchStrategy(**result).model_dump()

    await notify(ws, "stage_update", {
        "name": "strategy",
        "label": "Strategy",
        "status": "done",
        "todos": todos,
    })

    return {
        "strategy": strategy,
        "agent_traces": {
            **(state.get("agent_traces") or {}),
            "strategy": {"todos": todos},
        },
    }
