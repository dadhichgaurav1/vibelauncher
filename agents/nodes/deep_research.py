"""
Deep Research Agent.
Uses browser-use (via Chrome extension) to research viral X content in the product's niche.
Outputs a rich research_brief including content_strategy (format decision with rationale).
"""

from __future__ import annotations
import json
from state import VibeLaunchState
from nodes.base import llm_json, plan_todos
from tools.browser_client import browser_search_twitter, browser_get_page
from tools.ws_notifier import notify


RESEARCH_SYSTEM = """You are the Deep Research Agent for Vibe Launcher.

Your role: given a product brief and brainstorming context, research what works on X (Twitter)
for this specific niche, and produce a rich research_brief that drives all downstream content.

You have access to real Twitter research results. Analyze them deeply.

Apply X algorithm knowledge:
- Repost = 20x signal, Reply = 13.5x, Bookmark = 10x, Like = 1x
- Time decay: 50% visibility every 6 hours — early engagement velocity is everything
- No hashtags (algorithm doesn't boost them, looks spammy)
- External links in main post = deprioritized; always put links in first reply
- Native video gets 2-4x more reach than text-only
- Best posting: Tuesday/Wednesday 9-11 AM or 2-4 PM (adjust for niche)

Your output must include a content_strategy with format decision and clear rationale.
For each format (tweet, thread, image, video), decide: include or skip, and why.
Base this on: the product type, niche patterns you researched, ICP behavior on X.

Return valid JSON."""


CONTENT_STRATEGY_SYSTEM = """You are deciding what content formats to produce for an X launch.

Options: tweet, thread, image (carousel), video (30-45s)

Rules:
- At minimum, always produce a tweet
- Thread: use when product has depth worth explaining, or when builders/tech audience
- Image: use when product is visual, OR when competitor research shows images perform well in niche
- Video: use only when product has a compelling demo moment, motion, or before/after

Be decisive. For each format you skip, explain why concisely.
Return JSON: { "formats": [...], "rationale": { "tweet": "...", "thread": "...", "image": "...", "video": "..." } }
(null value for skipped formats' rationale means skip — still include the key)"""


async def run_deep_research(state: VibeLaunchState) -> dict:
    ws = state["ws_channel"]
    launch_id = state["launch_id"]
    product = state.get("product", {})
    brainstorm = state.get("brainstorm_responses", {})

    await notify(ws, "stage_update", {
        "name": "deep_research",
        "label": "Deep research",
        "status": "running",
        "todos": [],
    })

    product_name = product.get("name", "the product")
    features = product.get("features", [])
    audience = product.get("target_audience_signals", [])

    context = f"""Product: {product_name}
Features: {', '.join(features)}
Audience signals: {', '.join(audience)}
Brainstorm responses: {json.dumps(brainstorm)}"""

    # Step 1: Plan
    todos = await plan_todos(
        "deep_research",
        "Research X viral patterns for this product's niche, analyze competitors, define content strategy",
        context,
    )

    await notify(ws, "stage_update", {
        "name": "deep_research",
        "label": "Deep research",
        "status": "running",
        "todos": todos,
    })

    # Step 2: Execute browser research
    # Build search queries based on product
    search_queries = await _build_search_queries(product, brainstorm)
    research_data = []

    for i, query in enumerate(search_queries[:3]):  # cap at 3 searches
        # Mark todo in progress
        if i < len(todos):
            todos[i]["status"] = "in_progress"
            await notify(ws, "stage_update", {
                "name": "deep_research",
                "label": "Deep research",
                "status": "running",
                "todos": todos,
            })

        results = await browser_search_twitter(query, launch_id)
        research_data.append({"query": query, "results": results})

        if i < len(todos):
            todos[i]["status"] = "done"

    # Mark remaining todos done
    for todo in todos:
        if todo["status"] != "done":
            todo["status"] = "done"

    await notify(ws, "stage_update", {
        "name": "deep_research",
        "label": "Deep research",
        "status": "running",
        "todos": todos,
    })

    # Step 3: Synthesize research into brief
    research_brief = await llm_json(
        system=RESEARCH_SYSTEM,
        user=f"""Product context:
{context}

Browser research results:
{json.dumps(research_data, indent=2)[:4000]}

Produce a research_brief JSON with:
- icp: {{ "description": str, "pain_points": [str], "desires": [str], "x_behavior": str }}
- narrative_angles: [{{ "angle": str, "hook_example": str, "why_it_works": str }}] (3-5 angles)
- aesthetic_direction: {{ "aesthetic": str, "color_palette": [str], "style": str, "mood": str }}
- competitor_analysis: [{{ "account": str, "what_works": str, "engagement_pattern": str }}]
- viral_patterns: {{ "hook_styles": [str], "formats_that_work": [str], "engagement_triggers": [str] }}
- optimal_timing: {{ "day": str, "time": str, "timezone": str, "reasoning": str }}
- content_strategy: {{ "formats": [str], "rationale": {{ "tweet": str|null, "thread": str|null, "image": str|null, "video": str|null }} }}
""",
    )

    await notify(ws, "stage_update", {
        "name": "deep_research",
        "label": "Deep research",
        "status": "done",
        "todos": todos,
    })

    return {
        "research_brief": research_brief,
        "agent_traces": {
            **state.get("agent_traces", {}),
            "deep_research": {"todos": todos},
        },
    }


async def _build_search_queries(product: dict, brainstorm: dict) -> list[str]:
    """Generate targeted Twitter search queries for research."""
    name = product.get("name", "")
    audience = " ".join(product.get("target_audience_signals", []))
    icp = brainstorm.get("icp", "")

    result = await llm_json(
        system="Generate 3 Twitter/X search queries to research viral content in this product's niche. Focus on: competitor launches, audience pain points, viral content patterns. Return JSON: { 'queries': [str, str, str] }",
        user=f"Product: {name}\nAudience: {audience}\nICP context: {icp}",
    )
    return result.get("queries", [f"site:twitter.com {name} launch", f"{audience} tools launch"])
