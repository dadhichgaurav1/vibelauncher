"""Base agent class implementing Plan-then-Execute pattern."""

from __future__ import annotations
import json
from typing import Any
from openai import AsyncOpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def llm(
    system: str,
    user: str,
    response_format: dict | None = None,
    temperature: float = 0.7,
) -> str:
    """Single LLM call. Returns text or JSON string."""
    kwargs: dict[str, Any] = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
    }
    if response_format:
        kwargs["response_format"] = response_format

    resp = await client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


async def llm_json(system: str, user: str, temperature: float = 0.3) -> dict:
    """LLM call that returns parsed JSON."""
    raw = await llm(system, user, response_format={"type": "json_object"}, temperature=temperature)
    return json.loads(raw)


async def plan_todos(agent_name: str, task_description: str, context: str) -> list[dict]:
    """
    Ask the LLM to decompose the task into an ordered to-do list.
    Every agent calls this first before doing any work.
    """
    result = await llm_json(
        system=f"""You are the planning step for the {agent_name} agent.
Given a task description and context, decompose the work into a clear ordered list of to-do items.
Be specific and exhaustive — missing a step means it won't happen.
Return JSON: {{ "todos": [ {{ "id": 1, "task": "...", "status": "pending" }} ] }}""",
        user=f"Task: {task_description}\n\nContext:\n{context}",
    )
    return result.get("todos", [])
