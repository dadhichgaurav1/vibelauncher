"""
Content Creator Agent — generates tweet, thread, image prompts, video prompt.
Parallelizes all format LLM calls. Emits step_output for each format.
"""

from __future__ import annotations
import asyncio
import json
from state import VibeLaunchState, ContentBundle, TweetContent, ThreadContent, ThreadTweet, ImageContent, VideoContent
from nodes.base import llm_json
from tools.ws_notifier import notify


X_RULES = """MANDATORY X CONTENT RULES:
1. NO hashtags — ever.
2. NO "Like and RT" or "Retweet this" CTAs.
3. NO external links in the main tweet body — links go in first_reply ONLY.
4. Write like a sharp human, not a brand. No corporate-speak or AI slop.
5. One idea per tweet.
6. Hook tweet: first line must earn the second line. Most important tweet.
7. Thread midpoint (tweet 5-7): include genuine engagement trigger question.
8. Thread CTA (last tweet): recap + specific action.
9. Optimize for: reposts (20x) > replies (13.5x) > bookmarks (10x) > likes (1x).
10. Under 270 characters per tweet.

HOOK FORMULAS:
- Contrarian: "Most people think [X]. They're wrong."
- Specific Number: "I [analyzed/built/tested] [N]. Only [small number] [result]."
- Story: "[Time/event], [person] [did thing]. [consequence]."
- Bold Claim: "[Impressive result] in [timeframe]. Here's exactly how."
- Question: "What separates [X] from [Y]?"

Every piece must contain a shareable nugget that makes the sharer look smart."""


TWEET_SYSTEM = f"""You are writing a single launch tweet for X.

{X_RULES}

Write the tweet + a first_reply containing the product URL/link.
Return JSON: {{ "text": str, "char_count": int, "first_reply": str }}"""


THREAD_SYSTEM = f"""You are writing a launch thread for X.

{X_RULES}

Thread: 7-10 tweets. Tweet 1 = hook + "🧵". Midpoint = engagement trigger. Final = CTA.
Mark is_hook, is_cta, is_engagement_trigger. Add media_suggestion where relevant (2-3 max).

Return JSON: {{ "tweets": [{{ "position": int, "text": str, "char_count": int, "media_suggestion": str|null, "is_hook": bool, "is_cta": bool, "is_engagement_trigger": bool }}] }}"""


IMAGE_PROMPT_SYSTEM = """Write image generation prompts for a product launch on X.

Images must be non-generic, non-stock, non-AI-slop. Match the visual brief exactly.
High-performing types: cinematic product screenshots, mood shots, before/after comparisons, atmospheric scenes.

CRITICAL RULES FOR IMAGE PROMPTS:
- NEVER include hex color codes (like #FF5500) in prompts — the AI renders them as visible text
- NEVER include annotations, labels, arrows, or callout text
- NEVER ask for text overlays, watermarks, or UI mockup text
- Describe colors by name (warm amber, deep navy) not hex codes
- Focus on mood, composition, lighting, and subject matter
- Each prompt should produce a clean, professional image with NO text rendered in it

Generate 2-4 prompts.
Return JSON: { "images": [{ "prompt": str, "dimensions": "1200x675", "placement": str }] }"""


VIDEO_PROMPT_SYSTEM = """Write a video generation prompt for Veo (8-second clip).

The video is exactly 8 seconds. Hook in first 2 seconds. 9:16 vertical aspect ratio. 1080p.
Match the aesthetic direction exactly. Focus on one strong visual moment — don't try to cram a full story into 8 seconds.
Return JSON: { "prompt": str, "duration_seconds": 8, "aspect_ratio": "9:16" }"""


async def run_content_creator(state: VibeLaunchState, feedback: str | None = None) -> dict:
    ws = state["ws_channel"]
    product = state.get("product") or {}
    research = state.get("research_brief") or {}
    strategy = state.get("strategy") or {}

    formats = strategy.get("content_strategy", {}).get("formats", ["tweet"])
    visual_brief = strategy.get("visual_brief", {})
    narrative = strategy.get("narrative", "")
    icp = strategy.get("icp", "")
    tone = strategy.get("tone", "")

    todos = [{"id": i + 1, "task": f"Generate {fmt}", "status": "in_progress"} for i, fmt in enumerate(formats)]
    await notify(ws, "stage_update", {
        "name": "content_creator", "label": "Content creation", "status": "running", "todos": todos,
    })

    context = f"""Product: {json.dumps(product, indent=2)}
Narrative: {narrative}
ICP: {icp}
Tone: {tone}
Visual brief: {json.dumps(visual_brief, indent=2)}
Viral patterns: {json.dumps(research.get("viral_patterns", {}), indent=2)}
Formats to produce: {formats}"""
    if feedback:
        context += f"\n\nUSER FEEDBACK (must address): {feedback}"

    # Build all LLM tasks in parallel
    tasks: dict[str, asyncio.Task] = {}
    if "tweet" in formats:
        tasks["tweet"] = asyncio.create_task(llm_json(system=TWEET_SYSTEM, user=f"{context}\n\nWrite the launch tweet."))
    if "thread" in formats:
        tasks["thread"] = asyncio.create_task(llm_json(system=THREAD_SYSTEM, user=f"{context}\n\nWrite the launch thread (7-10 tweets)."))
    if "image" in formats:
        tasks["image"] = asyncio.create_task(llm_json(system=IMAGE_PROMPT_SYSTEM, user=f"{context}\n\nWrite image prompts tailored to the visual brief."))
    if "video" in formats:
        tasks["video"] = asyncio.create_task(llm_json(system=VIDEO_PROMPT_SYSTEM, user=f"{context}\n\nWrite the video prompt. Features: {product.get('features', [])}"))

    # Await all in parallel
    results: dict[str, dict] = {}
    for key, task in tasks.items():
        try:
            results[key] = await task
        except Exception as e:
            print(f"Content creator error for {key}: {e}")
            results[key] = {}

    content = ContentBundle()

    # Process results and emit step_output for each
    if "tweet" in results and results["tweet"]:
        td = results["tweet"]
        content.tweet = TweetContent(text=td.get("text", ""), char_count=len(td.get("text", "")), first_reply=td.get("first_reply"))
        await notify(ws, "step_output", {
            "stage": "content_creator", "step": "tweet_preview",
            "label": "Launch Tweet", "data": td, "type": "preview",
        })

    if "thread" in results and results["thread"]:
        tweets = [ThreadTweet(**t) for t in results["thread"].get("tweets", [])]
        content.thread = ThreadContent(tweets=tweets)
        await notify(ws, "step_output", {
            "stage": "content_creator", "step": "thread_preview",
            "label": "Launch Thread", "data": results["thread"], "type": "preview",
        })

    if "image" in results and results["image"]:
        content.images = [ImageContent(prompt=img["prompt"], dimensions=img.get("dimensions", "1200x675")) for img in results["image"].get("images", [])]
        await notify(ws, "step_output", {
            "stage": "content_creator", "step": "image_prompts",
            "label": "Image Prompts", "data": results["image"].get("images", []),
        })

    if "video" in results and results["video"]:
        content.video = VideoContent(prompt=results["video"].get("prompt", ""), duration_seconds=results["video"].get("duration_seconds", 30))
        await notify(ws, "step_output", {
            "stage": "content_creator", "step": "video_prompt",
            "label": "Video Prompt", "data": results["video"],
        })

    for t in todos:
        t["status"] = "done"
    await notify(ws, "stage_update", {
        "name": "content_creator", "label": "Content creation", "status": "done", "todos": todos,
    })

    return {
        "content": content.model_dump(),
        "agent_traces": {**(state.get("agent_traces") or {}), "content_creator": {"todos": todos}},
    }
