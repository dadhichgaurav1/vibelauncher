"""Publisher node — posts to X via API, or shows ready-to-publish if not connected."""

from __future__ import annotations
from datetime import datetime
from state import VibeLaunchState, PublishResult
from tools.ws_notifier import notify
from tools.x_api import post_tweet, post_thread, upload_media


async def run_publisher(state: VibeLaunchState) -> dict:
    print(f"[VibeLauncher] Publisher node started. approved={state.get('approved')}")
    ws = state["ws_channel"]
    content = state.get("content") or {}
    strategy = state.get("strategy") or {}
    access_token = state.get("x_access_token")
    access_token_secret = state.get("x_access_token_secret")

    # What the user chose to publish
    selected = set(state.get("selected_formats") or [])
    schedule_mode = state.get("schedule_mode") or "now"
    print(f"[VibeLauncher] X tokens present: access={bool(access_token)}, secret={bool(access_token_secret)}")
    print(f"[VibeLauncher] Selected formats: {selected}, schedule: {schedule_mode}")

    # Check if X is connected
    if not access_token or not access_token_secret:
        await notify(ws, "stage_update", {
            "name": "publisher", "label": "Publishing", "status": "done",
            "todos": [{"id": 1, "task": "Ready to publish (connect X to post)", "status": "done"}],
        })
        await notify(ws, "step_output", {
            "stage": "publisher", "step": "ready",
            "label": "Ready to Publish",
            "data": {
                "status": "ready",
                "message": "Your launch content is ready. Connect your X account to post automatically.",
                "selected_formats": list(selected),
                "schedule_mode": schedule_mode,
            },
        })
        await notify(ws, "phase", "published")

        result = PublishResult(posted_at=datetime.utcnow().isoformat())
        return {
            "published": result.model_dump(),
            "agent_traces": {**(state.get("agent_traces") or {}), "publisher": {"todos": []}},
        }

    # Handle scheduled posts
    if schedule_mode == "scheduled":
        posting_day = strategy.get("posting_day", "")
        posting_time = strategy.get("posting_time", "")
        timezone = strategy.get("timezone", "")
        schedule_label = f"{posting_day} at {posting_time} {timezone}"

        await notify(ws, "stage_update", {
            "name": "publisher", "label": "Publishing", "status": "done",
            "todos": [{"id": 1, "task": f"Scheduled for {schedule_label}", "status": "done"}],
        })
        await notify(ws, "step_output", {
            "stage": "publisher", "step": "scheduled",
            "label": "Scheduled",
            "data": {
                "status": "scheduled",
                "message": f"Your launch is scheduled for {schedule_label}.",
                "selected_formats": list(selected),
                "posting_day": posting_day,
                "posting_time": posting_time,
                "timezone": timezone,
            },
        })
        await notify(ws, "phase", "published")

        result = PublishResult(scheduled_at=f"{posting_day} {posting_time} {timezone}")
        return {
            "published": result.model_dump(),
            "agent_traces": {**(state.get("agent_traces") or {}), "publisher": {"todos": []}},
        }

    # X is connected, posting now — build dynamic todo list based on selections
    todos = []
    todo_id = 1

    has_images = "image" in selected and content.get("images")
    has_tweet = "tweet" in selected and content.get("tweet")
    has_thread = "thread" in selected and content.get("thread")

    if has_images:
        todos.append({"id": todo_id, "task": "Upload media", "status": "in_progress"})
        todo_id += 1
    if has_tweet:
        todos.append({"id": todo_id, "task": "Post tweet", "status": "pending"})
        todo_id += 1
    if has_thread:
        todos.append({"id": todo_id, "task": "Post thread", "status": "pending"})
        todo_id += 1

    if not todos:
        await notify(ws, "stage_update", {
            "name": "publisher", "label": "Publishing", "status": "done", "todos": [],
        })
        await notify(ws, "phase", "published")
        return {"published": PublishResult(posted_at=datetime.utcnow().isoformat()).model_dump()}

    await notify(ws, "stage_update", {
        "name": "publisher", "label": "Publishing", "status": "running", "todos": todos,
    })

    result = PublishResult()

    try:
        # Upload images if selected
        media_ids = []
        if has_images:
            for img in content["images"][:4]:
                if img.get("url") and not img["url"].startswith("data:"):
                    media_id = await upload_media(img["url"], access_token, access_token_secret)
                    if media_id:
                        media_ids.append(media_id)
            _mark_todo(todos, "Upload media", "done")
            await notify(ws, "stage_update", {
                "name": "publisher", "label": "Publishing", "status": "running", "todos": todos,
            })

        # Post tweet if selected
        if has_tweet:
            _mark_todo(todos, "Post tweet", "in_progress")
            await notify(ws, "stage_update", {
                "name": "publisher", "label": "Publishing", "status": "running", "todos": todos,
            })

            tweet_text = content["tweet"].get("text", "")
            first_reply_text = content["tweet"].get("first_reply", "")

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

            _mark_todo(todos, "Post tweet", "done")

        # Post thread if selected
        if has_thread:
            _mark_todo(todos, "Post thread", "in_progress")
            await notify(ws, "stage_update", {
                "name": "publisher", "label": "Publishing", "status": "running", "todos": todos,
            })

            thread_texts = [t["text"] for t in content["thread"].get("tweets", [])]
            thread_ids = await post_thread(
                tweets=thread_texts,
                access_token=access_token,
                access_token_secret=access_token_secret,
            )
            result.thread_ids = thread_ids
            _mark_todo(todos, "Post thread", "done")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Publishing error: {e}")
        await notify(ws, "stage_update", {
            "name": "publisher", "label": "Publishing", "status": "failed", "todos": todos,
        })
        await notify(ws, "phase", "published")
        return {"error": str(e)}

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


def _mark_todo(todos: list[dict], task: str, status: str):
    for t in todos:
        if t["task"] == task:
            t["status"] = status
            break
