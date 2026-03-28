"""
Deep Research Agent.
Uses browser-use to research viral X content. Emits step_output for each finding.
"""

from __future__ import annotations
import asyncio
import json
from state import VibeLaunchState
from nodes.base import llm_json
from tools.browser_client import browser_search_twitter
from tools.ws_notifier import notify


RESEARCH_SYSTEM = """You are the Deep Research Agent for Vibe Launcher.

Given a product brief and brainstorming context, plus real Twitter research results,
produce a rich research_brief that drives all downstream content.

X algorithm knowledge:
- Repost = 20x signal, Reply = 13.5x, Bookmark = 10x, Like = 1x
- Time decay: 50% visibility every 6 hours — early engagement velocity is everything
- No hashtags (algorithm doesn't boost them)
- External links in main post = deprioritized; put links in first reply
- Native video gets 2-4x more reach
- Best posting: Tuesday/Wednesday 9-11 AM or 2-4 PM

Your output must include a content_strategy with format decision and clear rationale.
For each format (tweet, thread, image, video), decide: include or skip, and why.

Return valid JSON."""


async def run_deep_research(state: VibeLaunchState) -> dict:
    ws = state["ws_channel"]
    launch_id = state["launch_id"]
    product = state.get("product") or {}
    brainstorm = state.get("brainstorm_responses") or {}

    todos = [
        {"id": 1, "task": "Search X for viral content in niche", "status": "in_progress"},
        {"id": 2, "task": "Analyze patterns and competitors", "status": "pending"},
        {"id": 3, "task": "Define ICP and content strategy", "status": "pending"},
    ]

    await notify(ws, "stage_update", {
        "name": "deep_research", "label": "Deep research", "status": "running", "todos": todos,
    })

    product_name = product.get("name", "the product")
    features = product.get("features", [])
    audience = product.get("target_audience_signals", [])

    context = f"""Product: {product_name}
Features: {', '.join(features)}
Audience signals: {', '.join(audience)}
Brainstorm responses: {json.dumps(brainstorm)}"""

    # Build search queries
    query_result = await llm_json(
        system="Generate 3 Twitter/X search queries to research viral content in this product's niche. Focus on: competitor launches, audience pain points, viral content patterns. Return JSON: { \"queries\": [str, str, str] }",
        user=f"Product: {product_name}\nAudience: {' '.join(audience)}\nBrainstorm: {json.dumps(brainstorm)}",
    )
    search_queries = query_result.get("queries", [f"{product_name} launch", f"{''.join(audience[:1])} tools"])

    # Parallel browser searches
    async def _search(query):
        return {"query": query, "results": await browser_search_twitter(query, launch_id)}

    research_data = await asyncio.gather(*[_search(q) for q in search_queries[:3]])

    todos[0]["status"] = "done"
    todos[1]["status"] = "in_progress"
    await notify(ws, "stage_update", {
        "name": "deep_research", "label": "Deep research", "status": "running", "todos": todos,
    })

    # Synthesize research
    research_brief = await llm_json(
        system=RESEARCH_SYSTEM,
        user=f"""Product context:\n{context}\n\nBrowser research results:\n{json.dumps(research_data, indent=2)[:4000]}\n\nProduce a research_brief JSON with:
- icp: {{ "description": str, "pain_points": [str], "desires": [str], "x_behavior": str }}
- narrative_angles: [{{ "angle": str, "hook_example": str, "why_it_works": str }}] (3-5 angles)
- aesthetic_direction: {{ "aesthetic": str, "color_palette": [str], "style": str, "mood": str }}
- competitor_analysis: [{{ "account": str, "what_works": str, "engagement_pattern": str }}]
- viral_patterns: {{ "hook_styles": [str], "formats_that_work": [str], "engagement_triggers": [str] }}
- optimal_timing: {{ "day": str, "time": str, "timezone": str, "reasoning": str }}
- content_strategy: {{ "formats": [str], "rationale": {{ "tweet": str|null, "thread": str|null, "image": str|null, "video": str|null }} }}
""",
    )

    todos[1]["status"] = "done"
    todos[2]["status"] = "in_progress"
    await notify(ws, "stage_update", {
        "name": "deep_research", "label": "Deep research", "status": "running", "todos": todos,
    })

    # Emit step_output for each research section
    for section, label in [
        ("icp", "Ideal Customer Profile"),
        ("narrative_angles", "Narrative Angles"),
        ("competitor_analysis", "Competitor Analysis"),
        ("viral_patterns", "Viral Patterns"),
        ("content_strategy", "Content Format Decisions"),
        ("optimal_timing", "Optimal Posting Time"),
    ]:
        if section in research_brief:
            await notify(ws, "step_output", {
                "stage": "deep_research", "step": section, "label": label,
                "data": research_brief[section],
            })

    todos[2]["status"] = "done"
    await notify(ws, "stage_update", {
        "name": "deep_research", "label": "Deep research", "status": "done", "todos": todos,
    })

    return {
        "research_brief": research_brief,
        "agent_traces": {**(state.get("agent_traces") or {}), "deep_research": {"todos": todos}},
    }
