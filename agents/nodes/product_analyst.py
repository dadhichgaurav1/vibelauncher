"""
Product Analyst node.
Reads all available inputs (URL via extension browser-use, markdown, transcript, readme)
and produces a structured ProductBrief.
"""

from __future__ import annotations
import json
from state import VibeLaunchState, ProductBrief
from nodes.base import llm_json, plan_todos
from tools.ws_notifier import notify


SYSTEM_PROMPT = """You are the Product Analyst agent for Vibe Launcher.

Your job: read everything provided about a product and extract a structured, accurate brief.

You will receive any combination of: product URL content, markdown descriptions, chat transcripts, READMEs.
Work with whatever you have — do not require all inputs to be present.

Extract:
- Product name (exact, not generic)
- Tagline (1 sharp sentence, not marketing fluff)
- Core features (3-7, specific and real — not "it's fast and easy")
- Target audience signals (who is this actually for, based on evidence in the inputs)
- Positioning notes (what makes it different, if detectable)

Be precise. Do not invent features not evidenced in the inputs.
Return JSON matching the ProductBrief schema."""


async def run_product_analyst(state: VibeLaunchState) -> dict:
    launch_id = state["launch_id"]
    ws = state["ws_channel"]

    await notify(ws, "stage_update", {
        "name": "product_analyst",
        "label": "Product analysis",
        "status": "running",
        "todos": [],
    })

    # Assemble all available inputs
    inputs: dict[str, str] = {}
    if state.get("input_url"):
        inputs["url"] = state["input_url"]
    if state.get("input_markdown"):
        inputs["markdown"] = state["input_markdown"]
    if state.get("input_transcript"):
        inputs["transcript"] = state["input_transcript"]
    if state.get("input_readme"):
        inputs["readme"] = state["input_readme"]

    # If URL provided, get page content via browser (extension or fallback)
    url_content = ""
    if state.get("input_url"):
        from tools.browser_client import fetch_page_content
        url_content = await fetch_page_content(state["input_url"], launch_id)
        if url_content:
            inputs["url_content"] = url_content

    context = json.dumps(inputs, indent=2)

    # Step 1: Plan todos
    todos = await plan_todos(
        "product_analyst",
        "Analyze all available product inputs and extract a structured ProductBrief",
        context[:2000],  # truncate context for planning step
    )

    await notify(ws, "stage_update", {
        "name": "product_analyst",
        "label": "Product analysis",
        "status": "running",
        "todos": todos,
    })

    # Step 2: Execute — work through each todo and produce the brief
    # Mark todos in progress as we go
    for i, todo in enumerate(todos):
        todos[i]["status"] = "in_progress"
        await notify(ws, "stage_update", {
            "name": "product_analyst",
            "label": "Product analysis",
            "status": "running",
            "todos": todos,
        })
        todos[i]["status"] = "done"

    # Main extraction
    result = await llm_json(
        system=SYSTEM_PROMPT,
        user=f"""Available inputs:

{context}

Return a ProductBrief JSON with fields:
- name (str)
- tagline (str)
- features (list of str)
- target_audience_signals (list of str)
- screenshots (list — leave empty if none available)
- url (str or null)
""",
    )

    product = ProductBrief(**result).model_dump()

    await notify(ws, "stage_update", {
        "name": "product_analyst",
        "label": "Product analysis",
        "status": "done",
        "todos": todos,
    })

    return {
        "product": product,
        "agent_traces": {
            **state.get("agent_traces", {}),
            "product_analyst": {"todos": todos},
        },
    }
