"""Product Analyst node — extracts structured ProductBrief from any input combination."""

from __future__ import annotations
import json
from state import VibeLaunchState, ProductBrief
from nodes.base import llm_json
from tools.ws_notifier import notify


SYSTEM_PROMPT = """You are the Product Analyst agent for Vibe Launcher.

Your job: read everything provided about a product and extract a structured, accurate brief.

You will receive any combination of: product URL content, markdown descriptions, chat transcripts, READMEs.
Work with whatever you have — do not require all inputs to be present.

Extract:
- Product name (exact, not generic)
- Tagline (1 sharp sentence, not marketing fluff)
- Core features (3-7, specific and real)
- Target audience signals (who is this actually for, based on evidence)
- Positioning notes (what makes it different)

Be precise. Do not invent features not evidenced in the inputs.
Return JSON matching the ProductBrief schema."""


async def run_product_analyst(state: VibeLaunchState) -> dict:
    launch_id = state["launch_id"]
    ws = state["ws_channel"]

    todos = [
        {"id": 1, "task": "Collect all available product inputs", "status": "in_progress"},
        {"id": 2, "task": "Extract product brief via AI analysis", "status": "pending"},
    ]

    await notify(ws, "stage_update", {
        "name": "product_analyst", "label": "Product analysis", "status": "running", "todos": todos,
    })

    # Assemble inputs
    inputs: dict[str, str] = {}
    if state.get("input_url"):
        inputs["url"] = state["input_url"]
    if state.get("input_markdown"):
        inputs["markdown"] = state["input_markdown"]
    if state.get("input_transcript"):
        inputs["transcript"] = state["input_transcript"]
    if state.get("input_readme"):
        inputs["readme"] = state["input_readme"]

    # Browser fetch if URL provided
    if state.get("input_url"):
        from tools.browser_client import fetch_page_content
        url_content = await fetch_page_content(state["input_url"], launch_id)
        if url_content:
            inputs["url_content"] = url_content

    todos[0]["status"] = "done"
    todos[1]["status"] = "in_progress"
    await notify(ws, "stage_update", {
        "name": "product_analyst", "label": "Product analysis", "status": "running", "todos": todos,
    })

    context = json.dumps(inputs, indent=2)

    result = await llm_json(
        system=SYSTEM_PROMPT,
        user=f"""Available inputs:\n\n{context}\n\nReturn a ProductBrief JSON with: name, tagline, features (list), target_audience_signals (list), screenshots (empty list), url (str or null)""",
    )

    product = ProductBrief(**result).model_dump()

    for t in todos:
        t["status"] = "done"
    await notify(ws, "stage_update", {
        "name": "product_analyst", "label": "Product analysis", "status": "done", "todos": todos,
    })

    # Emit visual step output
    await notify(ws, "step_output", {
        "stage": "product_analyst", "step": "product_brief", "label": "Product Brief",
        "data": product,
    })

    return {
        "product": product,
        "agent_traces": {**(state.get("agent_traces") or {}), "product_analyst": {"todos": todos}},
    }
