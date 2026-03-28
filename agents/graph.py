"""
LangGraph state graph for Vibe Launcher.
Orchestrates all agent nodes with critic review loops and human interrupts.
"""

from __future__ import annotations
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver as SqliteSaver

from state import VibeLaunchState
from nodes.product_analyst import run_product_analyst
from nodes.deep_research import run_deep_research
from nodes.strategy import run_strategy
from nodes.content_creator import run_content_creator
from nodes.media_generator import run_media_generator
from nodes.publisher import run_publisher
from nodes.critic import run_critic, should_retry
from tools.ws_notifier import notify


# ─── Node wrappers ───────────────────────────────────────────────────────────

async def product_analyst_node(state: VibeLaunchState) -> dict:
    updates = await run_product_analyst(state)
    # Run critic
    critique = await run_critic(
        state,
        stage="product_brief",
        output_to_review=updates.get("product", {}),
        completed_todos=updates.get("agent_traces", {}).get("product_analyst", {}).get("todos", []),
    )
    retry_counts = dict((state.get("retry_counts") or {}))
    if await should_retry(state, "product_brief", critique):
        retry_counts["product_brief"] = retry_counts.get("product_brief", 0) + 1
        return {**updates, "retry_counts": retry_counts, "_retry": "product_analyst"}
    return {
        **updates,
        "critiques": {**(state.get("critiques") or {}), "product_brief": critique.model_dump()},
        "retry_counts": retry_counts,
    }


async def brainstorm_node(state: VibeLaunchState) -> dict:
    """Generate brainstorm questions and interrupt for human input."""
    from nodes.base import llm_json
    product = state.get("product", {})

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

    await notify(state["ws_channel"], "brainstorm_prompt", brainstorm_data)
    await notify(state["ws_channel"], "phase", "brainstorm")

    return {"brainstorm_prompt": brainstorm_data}


async def deep_research_node(state: VibeLaunchState) -> dict:
    updates = await run_deep_research(state)
    critique = await run_critic(
        state,
        stage="research_brief",
        output_to_review=updates.get("research_brief", {}),
        completed_todos=updates.get("agent_traces", {}).get("deep_research", {}).get("todos", []),
    )
    retry_counts = dict((state.get("retry_counts") or {}))
    if await should_retry(state, "research_brief", critique):
        retry_counts["research_brief"] = retry_counts.get("research_brief", 0) + 1
        return {**updates, "retry_counts": retry_counts, "_retry": "deep_research"}
    return {
        **updates,
        "critiques": {**(state.get("critiques") or {}), "research_brief": critique.model_dump()},
        "retry_counts": retry_counts,
    }


async def strategy_node(state: VibeLaunchState) -> dict:
    updates = await run_strategy(state)
    critique = await run_critic(
        state,
        stage="strategy",
        output_to_review=updates.get("strategy", {}),
        completed_todos=updates.get("agent_traces", {}).get("strategy", {}).get("todos", []),
    )
    retry_counts = dict((state.get("retry_counts") or {}))
    if await should_retry(state, "strategy", critique):
        retry_counts["strategy"] = retry_counts.get("strategy", 0) + 1
        return {**updates, "retry_counts": retry_counts, "_retry": "strategy"}
    return {
        **updates,
        "critiques": {**(state.get("critiques") or {}), "strategy": critique.model_dump()},
        "retry_counts": retry_counts,
    }


async def content_creator_node(state: VibeLaunchState) -> dict:
    feedback = state.get("approval_feedback")
    updates = await run_content_creator(state, feedback=feedback)
    critique = await run_critic(
        state,
        stage="content",
        output_to_review=updates.get("content", {}),
        completed_todos=updates.get("agent_traces", {}).get("content_creator", {}).get("todos", []),
    )
    retry_counts = dict((state.get("retry_counts") or {}))
    if await should_retry(state, "content", critique):
        retry_counts["content"] = retry_counts.get("content", 0) + 1
        return {**updates, "retry_counts": retry_counts, "_retry": "content_creator",
                "approval_feedback": f"Critic notes: {'; '.join(critique.issues)}"}
    return {
        **updates,
        "critiques": {**(state.get("critiques") or {}), "content": critique.model_dump()},
        "retry_counts": retry_counts,
        "approval_feedback": None,
    }


async def media_generator_node(state: VibeLaunchState) -> dict:
    return await run_media_generator(state)


async def human_review_node(state: VibeLaunchState) -> dict:
    """Interrupt here for human review. Resumes when WebSocket sends approval."""
    await notify(state["ws_channel"], "content_ready", state.get("content", {}))
    await notify(state["ws_channel"], "phase", "review")
    # LangGraph interrupt — execution pauses here until resumed
    return {}


async def publisher_node(state: VibeLaunchState) -> dict:
    return await run_publisher(state)


# ─── Routing ─────────────────────────────────────────────────────────────────

def route_after_product_analyst(state: VibeLaunchState) -> str:
    if state.get("_retry") == "product_analyst":
        return "product_analyst"
    return "brainstorm"


def route_after_deep_research(state: VibeLaunchState) -> str:
    if state.get("_retry") == "deep_research":
        return "deep_research"
    return "strategy"


def route_after_strategy(state: VibeLaunchState) -> str:
    if state.get("_retry") == "strategy":
        return "strategy"
    return "content_creator"


def route_after_content(state: VibeLaunchState) -> str:
    if state.get("_retry") == "content_creator":
        return "content_creator"
    return "media_generator"


def route_after_review(state: VibeLaunchState) -> str:
    if state.get("approved"):
        return "publisher"
    # Not approved — loop back to content_creator with feedback
    return "content_creator"


# ─── Build graph ─────────────────────────────────────────────────────────────

def build_graph(checkpointer=None):
    builder = StateGraph(VibeLaunchState)

    # Add nodes
    builder.add_node("product_analyst", product_analyst_node)
    builder.add_node("brainstorm", brainstorm_node)
    builder.add_node("deep_research", deep_research_node)
    builder.add_node("strategy", strategy_node)
    builder.add_node("content_creator", content_creator_node)
    builder.add_node("media_generator", media_generator_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("publisher", publisher_node)

    # Entry
    builder.set_entry_point("product_analyst")

    # Edges with routing
    builder.add_conditional_edges("product_analyst", route_after_product_analyst,
                                   {"product_analyst": "product_analyst", "brainstorm": "brainstorm"})
    # Brainstorm → interrupt → deep_research (resumes after human input)
    builder.add_edge("brainstorm", "deep_research")

    builder.add_conditional_edges("deep_research", route_after_deep_research,
                                   {"deep_research": "deep_research", "strategy": "strategy"})
    builder.add_conditional_edges("strategy", route_after_strategy,
                                   {"strategy": "strategy", "content_creator": "content_creator"})
    builder.add_conditional_edges("content_creator", route_after_content,
                                   {"content_creator": "content_creator", "media_generator": "media_generator"})
    builder.add_edge("media_generator", "human_review")
    builder.add_conditional_edges("human_review", route_after_review,
                                   {"publisher": "publisher", "content_creator": "content_creator"})
    builder.add_edge("publisher", END)

    return builder.compile(
        checkpointer=checkpointer,
        interrupt_after=["brainstorm"],
        interrupt_before=["human_review"],
    )


# Graph is instantiated at server startup with an async checkpointer
