"""Base LLM call utilities."""

from __future__ import annotations
import json
import re
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

    try:
        resp = await client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""
    except Exception as e:
        # If response_format fails, retry without it
        if response_format:
            print(f"LLM call failed with response_format, retrying without: {e}")
            kwargs.pop("response_format", None)
            resp = await client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content or ""
        raise


async def llm_json(system: str, user: str, temperature: float = 0.3) -> dict:
    """LLM call that returns parsed JSON."""
    raw = await llm(
        system + "\n\nYou MUST respond with valid JSON only. No markdown, no code fences.",
        user,
        response_format={"type": "json_object"},
        temperature=temperature,
    )
    # Strip markdown code fences if present
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)
