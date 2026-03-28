"""
Critic Agent — reviews every major node's output before it passes downstream.
Called after: product_analyst, deep_research, strategy, content_creator.
Uses X Skill rubric for content review.
"""

from __future__ import annotations
import json
from state import VibeLaunchState, CritiqueResult
from nodes.base import llm_json
from tools.ws_notifier import notify


CRITIC_SYSTEM = """You are a sharp, exacting critic for Vibe Launcher.

Your job: review the output of an agent and determine if it meets the quality bar.
Be honest and specific — vague feedback helps no one.

Scoring rubric (0-10 for each):
- completeness: Did the agent complete all its todos? Is anything missing?
- accuracy: Does the output accurately reflect the inputs? Are there hallucinated details?
- specificity: Is the output specific to THIS product and audience, or generic?
- quality: Is this the best version, or is there a clear way to improve it?

For content specifically, also score:
- hook_quality: Does the hook stop the scroll? Does line 1 earn line 2?
- repost_worthy: Is there a shareable nugget (stat, framework, insight)?
- x_rules_compliance: No hashtags, no links in body, no "RT this" CTAs?
- icp_alignment: Does this speak directly to the defined ICP?

Pass threshold: average >= 7.5 out of 10, AND x_rules_compliance must be 10 if applicable.

Return JSON: {
  "pass": bool,
  "score": float,
  "issues": [str] (specific problems, empty if pass),
  "suggestions": [str] (specific improvements, empty if pass)
}"""


X_CONTENT_RUBRIC = """Additional X content rules to check:
- NO hashtags anywhere in the content
- NO external links in tweet body (links only in first_reply)
- NO "Like and RT" / "Retweet this" / "Share this" CTAs
- Hook (first line) must create cognitive dissonance, curiosity, or story tension
- Every tweet must be under 270 characters
- Thread must have engagement trigger at tweet 5-7
- Content must sound like a sharp human, not a brand account
- No generic phrases: "I'm excited to share", "game-changing", "revolutionary", "next-level"
"""


async def run_critic(
    state: VibeLaunchState,
    stage: str,
    output_to_review: dict,
    completed_todos: list[dict],
) -> CritiqueResult:
    """
    Review a specific stage output.
    stage: "product_brief" | "research_brief" | "strategy" | "content"
    """
    ws = state["ws_channel"]

    stage_contexts = {
        "product_brief": "Product analyst output — should be accurate, specific, non-generic",
        "research_brief": "Deep research output — should have real insights, specific patterns, accurate format decision",
        "strategy": "Launch strategy — should be tailored to product and ICP, not generic advice",
        "content": "Launch content — apply full X rules rubric",
    }

    extra_rules = X_CONTENT_RUBRIC if stage == "content" else ""

    result = await llm_json(
        system=CRITIC_SYSTEM,
        user=f"""Stage: {stage}
Context: {stage_contexts.get(stage, "")}
{extra_rules}

Completed todos by the agent:
{json.dumps(completed_todos, indent=2)}

Output to review:
{json.dumps(output_to_review, indent=2)[:3000]}

Review this output and return your critique JSON.""",
        temperature=0.2,
    )

    critique = CritiqueResult(
        **{"pass": result.get("pass", True), **{k: v for k, v in result.items() if k != "pass"}}
    )

    await notify(ws, "stage_update", {
        "name": f"critic_{stage}",
        "label": f"Critic: {stage}",
        "status": "done",
        "critique": critique.model_dump(by_alias=False),
    })

    return critique


async def should_retry(
    state: VibeLaunchState,
    stage: str,
    critique: CritiqueResult,
    max_retries: int = 2,
) -> bool:
    """Check if we should retry the stage or pass through."""
    retry_counts = state.get("retry_counts", {})
    current_retries = retry_counts.get(stage, 0)

    if critique.pass_:
        return False

    if current_retries >= max_retries:
        # Exceeded max retries — pass through with a flag
        return False

    return True
