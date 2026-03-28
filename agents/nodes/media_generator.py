"""
Media Generator node.
Calls Gemini (NanoBanana) for images and Veo for video.
Prompts are fully informed by deep_research aesthetic direction.
"""

from __future__ import annotations
import json
import base64
import httpx
from state import VibeLaunchState
from nodes.base import plan_todos
from tools.ws_notifier import notify
from config import GEMINI_API_KEY


GEMINI_IMAGE_URL = "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict"
GEMINI_VEO_URL = "https://generativelanguage.googleapis.com/v1beta/models/veo-2.0-generate-001:predictLongRunning"


async def run_media_generator(state: VibeLaunchState) -> dict:
    ws = state["ws_channel"]
    content = state.get("content", {})
    strategy = state.get("strategy", {})

    await notify(ws, "stage_update", {
        "name": "media_generator",
        "label": "Media generation",
        "status": "running",
        "todos": [],
    })

    visual_brief = strategy.get("visual_brief", {})
    images_data = content.get("images", [])
    video_data = content.get("video")

    context = f"Visual brief: {json.dumps(visual_brief)}\nFormats needed: images={bool(images_data)}, video={bool(video_data)}"

    todos = await plan_todos(
        "media_generator",
        "Generate images via Gemini and video via Veo based on content prompts",
        context,
    )

    await notify(ws, "stage_update", {
        "name": "media_generator",
        "label": "Media generation",
        "status": "running",
        "todos": todos,
    })

    updated_content = dict(content)

    # Generate images
    if images_data:
        updated_images = []
        for img in images_data:
            enriched_prompt = _enrich_image_prompt(img.get("prompt", ""), visual_brief)
            image_url = await _generate_image(enriched_prompt)
            updated_images.append({**img, "url": image_url})
        updated_content["images"] = updated_images

    # Generate video
    if video_data:
        enriched_video_prompt = _enrich_video_prompt(
            video_data.get("prompt", ""), visual_brief
        )
        video_url = await _generate_video(
            enriched_video_prompt,
            video_data.get("duration_seconds", 30),
        )
        updated_content["video"] = {**video_data, "url": video_url}

    for todo in todos:
        todo["status"] = "done"

    await notify(ws, "stage_update", {
        "name": "media_generator",
        "label": "Media generation",
        "status": "done",
        "todos": todos,
    })

    return {
        "content": updated_content,
        "agent_traces": {
            **(state.get("agent_traces") or {}),
            "media_generator": {"todos": todos},
        },
    }


def _enrich_image_prompt(base_prompt: str, visual_brief: dict) -> str:
    """Enrich the image prompt with aesthetic direction from research."""
    aesthetic = visual_brief.get("aesthetic", "")
    colors = ", ".join(visual_brief.get("color_palette", []))
    style = visual_brief.get("style", "")
    mood = visual_brief.get("mood", "")

    return f"""{base_prompt}

Style: {style}. Aesthetic: {aesthetic}. Mood: {mood}.
Color palette: {colors}.
High quality, professional, non-stock-photo look.
No watermarks, no generic corporate imagery.
1200x675 pixels, 16:9 aspect ratio."""


def _enrich_video_prompt(base_prompt: str, visual_brief: dict) -> str:
    """Enrich video prompt with visual direction."""
    aesthetic = visual_brief.get("aesthetic", "")
    mood = visual_brief.get("mood", "")

    return f"""{base_prompt}

Visual style: {aesthetic}. Mood: {mood}.
Hook in first 2 seconds. High production quality.
Captions/text overlays for sound-off viewing.
9:16 vertical format, 1080p."""


async def _generate_image(prompt: str) -> str | None:
    """Call Gemini Imagen API for image generation."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{GEMINI_IMAGE_URL}?key={GEMINI_API_KEY}",
                json={
                    "instances": [{"prompt": prompt}],
                    "parameters": {"sampleCount": 1},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            # Response has base64 encoded image
            predictions = data.get("predictions", [])
            if predictions and "bytesBase64Encoded" in predictions[0]:
                # In production: save to storage and return URL
                # For now: return data URL for preview
                b64 = predictions[0]["bytesBase64Encoded"]
                mime = predictions[0].get("mimeType", "image/png")
                return f"data:{mime};base64,{b64}"
    except Exception as e:
        print(f"Image generation error: {e}")
    return None


async def _generate_video(prompt: str, duration_seconds: int) -> str | None:
    """Call Veo API for video generation."""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Initiate long-running operation
            resp = await client.post(
                f"{GEMINI_VEO_URL}?key={GEMINI_API_KEY}",
                json={
                    "instances": [{
                        "prompt": prompt,
                        "duration": min(duration_seconds, 8),  # Veo 2 cap — update when Veo 3 available
                    }],
                    "parameters": {
                        "aspectRatio": "9:16",
                        "sampleCount": 1,
                    },
                },
            )
            resp.raise_for_status()
            operation = resp.json()
            op_name = operation.get("name")

            if not op_name:
                return None

            # Poll for completion
            import asyncio
            for _ in range(20):  # max 20 polls
                await asyncio.sleep(6)
                poll_resp = await client.get(
                    f"https://generativelanguage.googleapis.com/v1beta/{op_name}?key={GEMINI_API_KEY}"
                )
                poll_data = poll_resp.json()
                if poll_data.get("done"):
                    video_uri = (
                        poll_data.get("response", {})
                        .get("predictions", [{}])[0]
                        .get("video", {})
                        .get("uri")
                    )
                    return video_uri
    except Exception as e:
        print(f"Video generation error: {e}")
    return None
