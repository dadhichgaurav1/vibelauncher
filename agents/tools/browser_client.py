"""
Browser client — sends browser-use commands to the Chrome extension
and awaits results via WebSocket.

For hackathon: falls back to httpx if extension not connected.
"""

from __future__ import annotations
import asyncio
import httpx
import json
from typing import Any

# Extension command queue: launch_id -> asyncio.Queue
_command_queues: dict[str, asyncio.Queue] = {}
_result_queues: dict[str, asyncio.Queue] = {}
_extension_ws: dict[str, Any] = {}  # launch_id -> extension websocket


def register_extension(launch_id: str, ws) -> None:
    _extension_ws[launch_id] = ws
    _command_queues[launch_id] = asyncio.Queue()
    _result_queues[launch_id] = asyncio.Queue()


def unregister_extension(launch_id: str) -> None:
    _extension_ws.pop(launch_id, None)
    _command_queues.pop(launch_id, None)
    _result_queues.pop(launch_id, None)


async def _send_browser_command(launch_id: str, command: dict) -> dict | None:
    """Send a command to the extension and wait for result."""
    ws = _extension_ws.get(launch_id)
    if not ws:
        return None

    result_queue = _result_queues.get(launch_id)
    if not result_queue:
        return None

    try:
        await ws.send_text(json.dumps(command))
        result = await asyncio.wait_for(result_queue.get(), timeout=30.0)
        return result
    except asyncio.TimeoutError:
        return None
    except Exception:
        return None


async def receive_browser_result(launch_id: str, result: dict) -> None:
    """Called when extension sends back a result."""
    q = _result_queues.get(launch_id)
    if q:
        await q.put(result)


async def fetch_page_content(url: str, launch_id: str) -> str:
    """Fetch page content via extension browser-use or httpx fallback."""
    # Try extension first
    result = await _send_browser_command(launch_id, {
        "action": "fetch_page",
        "url": url,
    })
    if result and result.get("content"):
        return result["content"]

    # Fallback: direct httpx request
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            return resp.text[:10000]  # cap at 10k chars
    except Exception:
        return ""


async def browser_search_twitter(query: str, launch_id: str) -> list[dict]:
    """Search Twitter/X via extension or fallback to web search."""
    # Try extension (user's logged-in browser session)
    result = await _send_browser_command(launch_id, {
        "action": "search_twitter",
        "query": query,
    })
    if result and result.get("tweets"):
        return result["tweets"]

    # Fallback: search via httpx (public search)
    try:
        encoded = query.replace(" ", "+")
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"https://nitter.net/search?q={encoded}&f=tweets",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            # Parse nitter results (basic extraction)
            return _parse_nitter_results(resp.text, query)
    except Exception:
        return [{"note": f"Could not fetch results for: {query}"}]


async def browser_get_page(url: str, launch_id: str) -> str:
    """Get page content via extension."""
    result = await _send_browser_command(launch_id, {
        "action": "get_page",
        "url": url,
    })
    if result:
        return result.get("content", "")
    return ""


def _parse_nitter_results(html: str, query: str) -> list[dict]:
    """Basic HTML parsing for nitter search results."""
    import re
    tweets = []

    # Extract tweet text (basic regex — good enough for research signal)
    tweet_texts = re.findall(r'class="tweet-content[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
    for text in tweet_texts[:10]:
        clean = re.sub(r"<[^>]+>", "", text).strip()
        if clean:
            tweets.append({"text": clean, "source": "nitter", "query": query})

    return tweets
