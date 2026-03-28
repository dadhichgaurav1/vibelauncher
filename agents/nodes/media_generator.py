"""
Media Generator — calls Gemini for images, Veo for video.
Parallelizes image gen. Emits step_output for each media item.
"""

from __future__ import annotations
import asyncio
import json
import httpx
from state import VibeLaunchState
from tools.ws_notifier import notify
from config import GEMINI_API_KEY


GEMINI_IMAGE_URL = "https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict"
GEMINI_VEO_URL = "https://generativelanguage.googleapis.com/v1beta/models/veo-2.0-generate-001:predictLongRunning"


async def run_media_generator(state: VibeLaunchState) -> dict:
    ws = state["ws_channel"]
    content = state.get("content") or {}
    strategy = state.get("strategy") or {}

    visual_brief = strategy.get("visual_brief", {})
    images_data = content.get("images", [])
    video_data = content.get("video")

    has_images = bool(images_data)
    has_video = bool(video_data)

    if not has_images and not has_video:
        await notify(ws, "stage_update", {
            "name": "media_generator", "label": "Media generation", "status": "done", "todos": [],
        })
        return {"agent_traces": {**(state.get("agent_traces") or {}), "media_generator": {"todos": []}}}

    todos = []
    if has_images:
        todos.append({"id": 1, "task": f"Generate {len(images_data)} images", "status": "in_progress"})
    if has_video:
        todos.append({"id": 2, "task": "Generate video", "status": "in_progress"})

    await notify(ws, "stage_update", {
        "name": "media_generator", "label": "Media generation", "status": "running", "todos": todos,
    })

    updated_content = dict(content)

    # Start video generation early (long-running) in parallel with images
    video_task = None
    if has_video:
        enriched_video = _enrich_video_prompt(video_data.get("prompt", ""), visual_brief)
        video_task = asyncio.create_task(_generate_video(enriched_video, video_data.get("duration_seconds", 30)))
        await notify(ws, "step_output", {
            "stage": "media_generator", "step": "video_status",
            "label": "Video", "data": {"status": "generating", "prompt": video_data.get("prompt", "")}, "type": "status",
        })

    # Generate images in parallel
    if has_images:
        async def gen_one(i, img):
            enriched = _enrich_image_prompt(img.get("prompt", ""), visual_brief)
            url = await _generate_image(enriched)
            await notify(ws, "step_output", {
                "stage": "media_generator", "step": f"image_{i}",
                "label": f"Image {i + 1}", "data": {"prompt": img.get("prompt", ""), "url": url}, "type": "image",
            })
            return {**img, "url": url}

        updated_images = await asyncio.gather(*[gen_one(i, img) for i, img in enumerate(images_data)])
        updated_content["images"] = list(updated_images)
        for t in todos:
            if t["id"] == 1:
                t["status"] = "done"

    # Await video
    if video_task:
        video_url = await video_task
        updated_content["video"] = {**video_data, "url": video_url}
        await notify(ws, "step_output", {
            "stage": "media_generator", "step": "video_status",
            "label": "Video", "data": {"status": "complete", "url": video_url, "prompt": video_data.get("prompt", "")}, "type": "status",
        })
        for t in todos:
            if t["id"] == 2:
                t["status"] = "done"

    await notify(ws, "stage_update", {
        "name": "media_generator", "label": "Media generation", "status": "done", "todos": todos,
    })

    return {
        "content": updated_content,
        "agent_traces": {**(state.get("agent_traces") or {}), "media_generator": {"todos": todos}},
    }


def _enrich_image_prompt(base_prompt: str, visual_brief: dict) -> str:
    """Enrich prompt with natural language only — no hex codes, no technical metadata."""
    aesthetic = visual_brief.get("aesthetic", "")
    style = visual_brief.get("style", "")
    mood = visual_brief.get("mood", "")
    # Deliberately exclude hex color codes — Imagen renders them as text
    return f"""{base_prompt}. {style} style, {aesthetic} aesthetic, {mood} mood. High quality professional photograph, no text, no watermarks, no annotations, no labels, no hex codes."""


def _enrich_video_prompt(base_prompt: str, visual_brief: dict) -> str:
    aesthetic = visual_brief.get("aesthetic", "")
    mood = visual_brief.get("mood", "")
    return f"""{base_prompt}. {aesthetic} aesthetic, {mood} mood. Cinematic, smooth motion, no text overlays."""


async def _generate_image(prompt: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{GEMINI_IMAGE_URL}?key={GEMINI_API_KEY}",
                json={"instances": [{"prompt": prompt}], "parameters": {"sampleCount": 1}},
            )
            resp.raise_for_status()
            data = resp.json()
            predictions = data.get("predictions", [])
            if predictions and "bytesBase64Encoded" in predictions[0]:
                b64 = predictions[0]["bytesBase64Encoded"]
                mime = predictions[0].get("mimeType", "image/png")
                return f"data:{mime};base64,{b64}"
    except Exception as e:
        print(f"Image generation error: {e}")
    return None


async def _generate_video(prompt: str, duration_seconds: int) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{GEMINI_VEO_URL}?key={GEMINI_API_KEY}",
                json={
                    "instances": [{"prompt": prompt}],
                    "parameters": {"aspectRatio": "9:16", "sampleCount": 1},
                },
            )
            resp.raise_for_status()
            operation = resp.json()
            op_name = operation.get("name")
            if not op_name:
                return None

            for _ in range(20):
                await asyncio.sleep(6)
                poll_resp = await client.get(
                    f"https://generativelanguage.googleapis.com/v1beta/{op_name}?key={GEMINI_API_KEY}"
                )
                poll_data = poll_resp.json()
                if poll_data.get("done"):
                    return poll_data.get("response", {}).get("predictions", [{}])[0].get("video", {}).get("uri")
    except Exception as e:
        print(f"Video generation error: {e}")
    return None
