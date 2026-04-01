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
from nodes.critic import run_critic, should_retry
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
    critic_feedback = state.get("critic_feedback")
    combined_feedback = " | ".join(filter(None, [feedback, critic_feedback]))
    updates = await run_content_creator(state, feedback=combined_feedback or None)
    return {**updates, "approval_feedback": None, "critic_feedback": None}


async def media_generator_node(state: VibeLaunchState) -> dict:
    return await run_media_generator(state)


async def critic_node(state: VibeLaunchState) -> dict:
    """Run critic on content, decide whether to retry or proceed."""
    content = state.get("content") or {}
    agent_traces = state.get("agent_traces") or {}
    content_todos = agent_traces.get("content_creator", {}).get("todos", [])

    critique = await run_critic(state, stage="content", output_to_review=content, completed_todos=content_todos)

    critiques = state.get("critiques") or {}
    critiques["content"] = critique.model_dump(by_alias=True)

    retry_counts = dict(state.get("retry_counts") or {})
    should = await should_retry(state, stage="content", critique=critique, max_retries=2)

    updates: dict = {"critiques": critiques}

    if should:
        retry_counts["content"] = retry_counts.get("content", 0) + 1
        updates["retry_counts"] = retry_counts
        feedback_parts = []
        if critique.issues:
            feedback_parts.append("Issues: " + "; ".join(critique.issues))
        if critique.suggestions:
            feedback_parts.append("Suggestions: " + "; ".join(critique.suggestions))
        updates["critic_feedback"] = " | ".join(feedback_parts) if feedback_parts else "Improve quality."
    else:
        updates["retry_counts"] = retry_counts

    # Emit critic scores via WebSocket for frontend
    ws = state["ws_channel"]
    await notify(ws, "step_output", {
        "stage": "critic",
        "step": "content_review",
        "label": "Content Quality Review",
        "data": {
            "pass": critique.pass_,
            "score": critique.score,
            "issues": critique.issues,
            "suggestions": critique.suggestions,
            "retry": should,
            "retry_count": retry_counts.get("content", 0),
        },
        "type": "card",
    })

    return updates


def route_after_critic(state: VibeLaunchState) -> str:
    """Route after critic: retry content_creator or proceed to human_review."""
    critiques = state.get("critiques") or {}
    content_critique = critiques.get("content", {})
    retry_counts = state.get("retry_counts") or {}

    if not content_critique.get("pass", True) and retry_counts.get("content", 0) <= 2:
        # Check if we just incremented — if critic_feedback is set, we need to retry
        if state.get("critic_feedback"):
            return "content_creator"
    return "human_review"


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
    builder.add_node("critic", critic_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("publisher", publisher_node)

    builder.set_entry_point("product_analyst")

    builder.add_edge("product_analyst", "brainstorm")
    builder.add_edge("brainstorm", "deep_research")
    builder.add_edge("deep_research", "strategy")
    builder.add_edge("strategy", "content_creator")
    builder.add_edge("content_creator", "media_generator")
    builder.add_edge("media_generator", "critic")
    builder.add_conditional_edges("critic", route_after_critic,
                                   {"content_creator": "content_creator", "human_review": "human_review"})
    builder.add_conditional_edges("human_review", route_after_review,
                                   {"publisher": "publisher", "content_creator": "content_creator"})
    builder.add_edge("publisher", END)

    return builder.compile(
        checkpointer=checkpointer,
        interrupt_after=["brainstorm"],
        interrupt_before=["human_review"],
    )
