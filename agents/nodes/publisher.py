"""Publisher node — posts to X via API, or shows ready-to-publish if not connected."""

from __future__ import annotations
from state import VibeLaunchState, PublishResult
from tools.ws_notifier import notify
from tools.x_api import post_tweet, post_thread, upload_media


async def run_publisher(state: VibeLaunchState) -> dict:
    ws = state["ws_channel"]
    content = state.get("content") or {}
    strategy = state.get("strategy") or {}
    access_token = state.get("x_access_token")
    access_token_secret = state.get("x_access_token_secret")

    # Check if X is connected
    if not access_token or not access_token_secret:
        # No X connected — mark as ready to publish (demo mode)
        await notify(ws, "stage_update", {
            "name": "publisher", "label": "Publishing", "status": "done",
            "todos": [{"id": 1, "task": "Ready to publish (connect X to post)", "status": "done"}],
        })
        await notify(ws, "step_output", {
            "stage": "publisher", "step": "ready",
            "label": "Ready to Publish",
            "data": {"status": "ready", "message": "Your launch content is ready. Connect your X account to post automatically."},
        })
        await notify(ws, "phase", "published")

        from datetime import datetime
        result = PublishResult(posted_at=datetime.utcnow().isoformat())
        return {
            "published": result.model_dump(),
            "agent_traces": {**(state.get("agent_traces") or {}), "publisher": {"todos": []}},
        }

    # X is connected — actually post
    todos = [
        {"id": 1, "task": "Upload media", "status": "in_progress"},
        {"id": 2, "task": "Post tweet", "status": "pending"},
        {"id": 3, "task": "Post thread", "status": "pending"},
    ]

    await notify(ws, "stage_update", {
        "name": "publisher", "label": "Publishing", "status": "running", "todos": todos,
    })

    formats = strategy.get("content_strategy", {}).get("formats", [])
    result = PublishResult()

    try:
        media_ids = []
        if content.get("images"):
            for img in content["images"][:4]:
                if img.get("url") and not img["url"].startswith("data:"):
                    media_id = await upload_media(img["url"], access_token, access_token_secret)
                    if media_id:
                        media_ids.append(media_id)

        todos[0]["status"] = "done"
        todos[1]["status"] = "in_progress"
        await notify(ws, "stage_update", {
            "name": "publisher", "label": "Publishing", "status": "running", "todos": todos,
        })

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

            if first_reply_text and tweet_id:
                await post_tweet(
                    text=first_reply_text,
                    reply_to_id=tweet_id,
                    access_token=access_token,
                    access_token_secret=access_token_secret,
                )

        todos[1]["status"] = "done"
        todos[2]["status"] = "in_progress"

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
            "name": "publisher", "label": "Publishing", "status": "failed", "todos": todos,
        })
        return {"error": str(e)}

    from datetime import datetime
    result.posted_at = datetime.utcnow().isoformat()

    for t in todos:
        t["status"] = "done"

    await notify(ws, "stage_update", {
        "name": "publisher", "label": "Publishing", "status": "done", "todos": todos,
    })
    await notify(ws, "phase", "published")

    return {
        "published": result.model_dump(),
        "agent_traces": {**(state.get("agent_traces") or {}), "publisher": {"todos": todos}},
    }
