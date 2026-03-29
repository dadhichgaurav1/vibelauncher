"""
LangGraph state graph for Vibe Launcher.
Orchestrates all agent nodes with human interrupts.
"""

from __future__ import annotations
from langgraph.graph import StateGraph, END

from state import VibeLaunchState
from nodes.product_analyst import run_product_analyst
from nodes.deep_research import run_deep_research
from nodes.strategy import run_strategy
from nodes.content_creator import run_content_creator
from nodes.media_generator import run_media_generator
from nodes.publisher import run_publisher
from tools.ws_notifier import notify


# ─── Node wrappers ───────────────────────────────────────────────────────────

async def product_analyst_node(state: VibeLaunchState) -> dict:
    return await run_product_analyst(state)


async def brainstorm_node(state: VibeLaunchState) -> dict:
    """Generate brainstorm questions and interrupt for human input."""
    from nodes.base import llm_json
    ws = state["ws_channel"]
    product = state.get("product") or {}

    await notify(ws, "stage_update", {
        "name": "human_brainstorm",
        "label": "Brainstorm",
        "status": "running",
        "todos": [{"id": 1, "task": "Generate brainstorm questions", "status": "in_progress"}],
    })

    brainstorm_data = await llm_json(
        system="""You are generating a smart brainstorm questionnaire for a product launch.
Given what we know about the product, ask 3-5 targeted questions that will help us nail:
1. The ICP (who exactly is this for?)
2. The narrative angle (what's the story?)
3. The tone (how does the builder want to come across?)

Use prompted options where helpful, but always allow custom answers.
Questions should be smart, not generic.

Return JSON: {
  "product_understanding": str (2-3 sentences summarizing what we understand),
  "questions": [
    {
      "id": str,
      "question": str,
      "options": [str] (3-5 options or empty for open-ended),
      "allow_custom": true,
      "type": "single" | "multi" | "text"
    }
  ]
}""",
        user=f"Product brief:\n{str(product)}\n\nGenerate smart brainstorm questions.",
    )

    await notify(ws, "stage_update", {
        "name": "human_brainstorm",
        "label": "Brainstorm",
        "status": "running",
        "todos": [
            {"id": 1, "task": "Generate brainstorm questions", "status": "done"},
            {"id": 2, "task": "Waiting for your input", "status": "in_progress"},
        ],
    })

    await notify(ws, "brainstorm_prompt", brainstorm_data)
    await notify(ws, "phase", "brainstorm")

    return {"brainstorm_prompt": brainstorm_data}


async def deep_research_node(state: VibeLaunchState) -> dict:
    return await run_deep_research(state)


async def strategy_node(state: VibeLaunchState) -> dict:
    return await run_strategy(state)


async def content_creator_node(state: VibeLaunchState) -> dict:
    feedback = state.get("approval_feedback")
    updates = await run_content_creator(state, feedback=feedback)
    return {**updates, "approval_feedback": None}


async def media_generator_node(state: VibeLaunchState) -> dict:
    return await run_media_generator(state)


async def human_review_node(state: VibeLaunchState) -> dict:
    """Interrupt here for human review. Notifications handled by server.py."""
    return {}


async def publisher_node(state: VibeLaunchState) -> dict:
    return await run_publisher(state)


# ─── Routing ─────────────────────────────────────────────────────────────────

def route_after_review(state: VibeLaunchState) -> str:
    if state.get("approved"):
        return "publisher"
    return "content_creator"


# ─── Build graph ─────────────────────────────────────────────────────────────

def build_graph(checkpointer=None):
    builder = StateGraph(VibeLaunchState)

    builder.add_node("product_analyst", product_analyst_node)
    builder.add_node("brainstorm", brainstorm_node)
    builder.add_node("deep_research", deep_research_node)
    builder.add_node("strategy", strategy_node)
    builder.add_node("content_creator", content_creator_node)
    builder.add_node("media_generator", media_generator_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("publisher", publisher_node)

    builder.set_entry_point("product_analyst")

    # Direct edges — no critic loops
    builder.add_edge("product_analyst", "brainstorm")
    builder.add_edge("brainstorm", "deep_research")
    builder.add_edge("deep_research", "strategy")
    builder.add_edge("strategy", "content_creator")
    builder.add_edge("content_creator", "media_generator")
    builder.add_edge("media_generator", "human_review")
    builder.add_conditional_edges("human_review", route_after_review,
                                   {"publisher": "publisher", "content_creator": "content_creator"})
    builder.add_edge("publisher", END)

    return builder.compile(
        checkpointer=checkpointer,
        interrupt_after=["brainstorm"],
        interrupt_before=["human_review"],
    )
