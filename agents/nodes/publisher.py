"""
Publisher node.
Posts to X via API. Handles tweet + thread + media.
Puts product links in first reply (never in main post body — X algorithm rule).
"""

from __future__ import annotations
import json
from state import VibeLaunchState, PublishResult
from nodes.base import plan_todos
from tools.ws_notifier import notify
from tools.x_api import post_tweet, post_thread, upload_media, schedule_tweet


async def run_publisher(state: VibeLaunchState) -> dict:
    ws = state["ws_channel"]
    content = state.get("content", {})
    strategy = state.get("strategy", {})
    access_token = state.get("x_access_token")
    access_token_secret = state.get("x_access_token_secret")

    await notify(ws, "stage_update", {
        "name": "publisher",
        "label": "Publishing",
        "status": "running",
        "todos": [],
    })

    formats = strategy.get("content_strategy", {}).get("formats", [])
    posting_day = strategy.get("posting_day", "Tuesday")
    posting_time = strategy.get("posting_time", "9:00 AM")
    timezone = strategy.get("timezone", "ET")

    context = f"Publishing formats: {formats}. Schedule: {posting_day} {posting_time} {timezone}"
    todos = await plan_todos("publisher", "Post content to X via API", context)

    await notify(ws, "stage_update", {
        "name": "publisher",
        "label": "Publishing",
        "status": "running",
        "todos": todos,
    })

    result = PublishResult()

    try:
        # Upload media first if we have images
        media_ids = []
        if content.get("images"):
            for img in content["images"][:4]:  # X max 4 images
                if img.get("url"):
                    media_id = await upload_media(
                        img["url"], access_token, access_token_secret
                    )
                    if media_id:
                        media_ids.append(media_id)

        # Post main tweet (with media if available)
        tweet_text = content.get("tweet", {}).get("text", "")
        first_reply_text = content.get("tweet", {}).get("first_reply", "")

        if tweet_text:
            tweet_id = await post_tweet(
                text=tweet_text,
                media_ids=media_ids if media_ids else None,
                access_token=access_token,
                access_token_secret=access_token_secret,
            )
            result.tweet_id = tweet_id

            # Post first reply with product link
            if first_reply_text and tweet_id:
                await post_tweet(
                    text=first_reply_text,
                    reply_to_id=tweet_id,
                    access_token=access_token,
                    access_token_secret=access_token_secret,
                )

        # Post thread if included
        if content.get("thread") and "thread" in formats:
            thread_texts = [t["text"] for t in content["thread"].get("tweets", [])]
            thread_ids = await post_thread(
                tweets=thread_texts,
                access_token=access_token,
                access_token_secret=access_token_secret,
            )
            result.thread_ids = thread_ids

    except Exception as e:
        print(f"Publishing error: {e}")
        await notify(ws, "stage_update", {
            "name": "publisher",
            "label": "Publishing",
            "status": "failed",
            "todos": todos,
        })
        return {"error": str(e)}

    from datetime import datetime
    result.posted_at = datetime.utcnow().isoformat()

    for todo in todos:
        todo["status"] = "done"

    await notify(ws, "stage_update", {
        "name": "publisher",
        "label": "Publishing",
        "status": "done",
        "todos": todos,
    })
    await notify(ws, "phase", "published")

    return {
        "published": result.model_dump(),
        "agent_traces": {
            **(state.get("agent_traces") or {}),
            "publisher": {"todos": todos},
        },
    }
