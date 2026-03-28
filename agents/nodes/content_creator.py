"""
Content Creator Agent.
Creates tweet, thread, image prompts, and video prompt based on strategy + research.
Only creates formats decided by research brief's content_strategy.
Applies X Skill rules strictly.
"""

from __future__ import annotations
import json
from state import VibeLaunchState, ContentBundle, TweetContent, ThreadContent, ThreadTweet
from nodes.base import llm_json, plan_todos
from tools.ws_notifier import notify


X_RULES = """MANDATORY X CONTENT RULES (never violate these):
1. NO hashtags — ever. The algorithm doesn't boost them; they look spammy.
2. NO "Like and RT" or "Retweet this" CTAs — spam filter trigger.
3. NO external links in the main tweet body — always put links in first_reply.
4. External links go in first_reply ONLY.
5. NO corporate-speak, marketing fluff, or "AI slop" language.
6. Write like a sharp human, not a brand.
7. One idea per tweet. If it needs two ideas, it's two tweets.
8. Hook tweet: the first line must earn the second line. This is the most important tweet.
9. Spend maximum effort on the hook — it determines if anyone reads the rest.
10. Thread midpoint (tweet 5-7): include a genuine question or engagement trigger.
11. Thread CTA (last tweet): recap + specific action + optional repost of tweet 1.
12. Optimize for: reposts (20x signal) > replies (13.5x) > bookmarks (10x) > likes (1x).
13. Under 270 characters per tweet (leave room for metadata).

HOOK FORMULAS (use one that fits):
- The Contrarian: "Most people think [X]. They're wrong."
- The Specific Number: "I [analyzed/built/tested] [N]. Only [small number] [result]."
- The Story Open: "[Specific time/event], [person] [did thing]. [consequence]."
- The Bold Claim: "[Impressive result] in [timeframe]. Here's exactly how."
- The Question: "What separates [X] from [Y]?"

SHAREABLE NUGGET: Every piece must contain one stat, insight, or framing that makes the sharer look smart."""


TWEET_SYSTEM = f"""You are writing a single launch tweet for a product on X (Twitter).

{X_RULES}

This tweet must:
- Stop the scroll in the first line
- Have a "shareable nugget" (stat, framework, or insight people want to repost)
- End with something that invites genuine replies (question, debate, or gap left intentionally)
- Not mention the product URL in the tweet body (it goes in first_reply)

Also write a first_reply that contains the product URL/link and a 1-line CTA.
Return JSON: {{ "text": str, "char_count": int, "first_reply": str }}"""


THREAD_SYSTEM = f"""You are writing a launch thread for a product on X (Twitter).

{X_RULES}

Thread requirements:
- Tweet 1 (hook): Must be the strongest thing you write. Pattern interrupt + value promise + "🧵"
- Tweets 2-N (body): Each tweet delivers ONE complete idea, compels reading the next
- Tweet ~5-7: Insert a genuine engagement trigger question (re-engages readers midway)
- Final tweet: TL;DR recap + specific CTA (follow/bookmark/reply). Repost tweet 1 link optional.
- 7-10 tweets is the sweet spot for builder/tech audiences
- Mark is_hook, is_cta, is_engagement_trigger on appropriate tweets
- media_suggestion: note where an image would boost a specific tweet (2-3 max in the thread)

Return JSON: {{ "tweets": [{{ "position": int, "text": str, "char_count": int, "media_suggestion": str|null, "is_hook": bool, "is_cta": bool, "is_engagement_trigger": bool }}] }}"""


IMAGE_PROMPT_SYSTEM = """You are writing image generation prompts for a product launch on X.

Images must:
- Be non-generic, non-stock-photo, non-AI-slop
- Reflect the specific aesthetic direction from the visual brief
- Use the exact color palette specified
- Be tailored to the ICP and narrative
- Match one of these high-performing types:
  * Data visualization / chart showing a result
  * Before/after comparison
  * Annotated screenshot (product UI with highlights)
  * Quote card (striking stat on clean background)
  * Framework/process visualization

Each prompt must specify: style, composition, colors, mood, and what specific element to include.
Generate 2-4 image prompts based on content formats being produced.
Return JSON: { "images": [{ "prompt": str, "dimensions": "1200x675", "placement": str }] }"""


VIDEO_PROMPT_SYSTEM = """You are writing a video generation prompt for Veo (Google's AI video generator).

Video requirements:
- 30-45 seconds if possible, or up to what Veo supports
- Must hook in first 2 seconds (visual motion, text, or face)
- Captions/text overlays burned in (many watch sound-off)
- 9:16 aspect ratio for mobile-first (or 16:9 if product is desktop-focused)
- 1080p quality
- Match the aesthetic direction exactly

High-performing video types for product launches:
- Screen recording with narration (if product has UI to demo)
- Before/after reveal
- "How we built this" behind-the-scenes
- Data visualization animated

Return JSON: { "prompt": str, "duration_seconds": 30, "aspect_ratio": "9:16" }"""


async def run_content_creator(state: VibeLaunchState, feedback: str | None = None) -> dict:
    ws = state["ws_channel"]
    product = state.get("product", {})
    research = state.get("research_brief", {})
    strategy = state.get("strategy", {})

    await notify(ws, "stage_update", {
        "name": "content_creator",
        "label": "Content creation",
        "status": "running",
        "todos": [],
    })

    formats = strategy.get("content_strategy", {}).get("formats", ["tweet"])
    visual_brief = strategy.get("visual_brief", {})
    icp = strategy.get("icp", "")
    narrative = strategy.get("narrative", "")
    tone = strategy.get("tone", "")

    context = f"""Product: {json.dumps(product, indent=2)}
Narrative: {narrative}
ICP: {icp}
Tone: {tone}
Visual brief: {json.dumps(visual_brief, indent=2)}
Viral patterns from research: {json.dumps(research.get("viral_patterns", {}), indent=2)}
Formats to produce: {formats}"""

    if feedback:
        context += f"\n\nUSER FEEDBACK (must address): {feedback}"

    todos = await plan_todos(
        "content_creator",
        f"Create content for formats: {', '.join(formats)}. Apply all X rules strictly.",
        context[:1500],
    )

    await notify(ws, "stage_update", {
        "name": "content_creator",
        "label": "Content creation",
        "status": "running",
        "todos": todos,
    })

    content = ContentBundle()

    # Create each format in the decided list
    if "tweet" in formats:
        tweet_data = await llm_json(
            system=TWEET_SYSTEM,
            user=f"{context}\n\nWrite the launch tweet.",
        )
        content.tweet = TweetContent(
            text=tweet_data["text"],
            char_count=len(tweet_data["text"]),
            first_reply=tweet_data.get("first_reply"),
        )

    if "thread" in formats:
        thread_data = await llm_json(
            system=THREAD_SYSTEM,
            user=f"{context}\n\nWrite the launch thread (7-10 tweets).",
        )
        tweets = [ThreadTweet(**t) for t in thread_data.get("tweets", [])]
        content.thread = ThreadContent(tweets=tweets)

    if "image" in formats:
        image_data = await llm_json(
            system=IMAGE_PROMPT_SYSTEM,
            user=f"{context}\n\nWrite image generation prompts tailored to the visual brief and narrative.",
        )
        from state import ImageContent
        content.images = [
            ImageContent(prompt=img["prompt"], dimensions=img.get("dimensions", "1200x675"))
            for img in image_data.get("images", [])
        ]

    if "video" in formats:
        video_data = await llm_json(
            system=VIDEO_PROMPT_SYSTEM,
            user=f"{context}\n\nWrite the video generation prompt. Product has these features: {product.get('features', [])}",
        )
        from state import VideoContent
        content.video = VideoContent(
            prompt=video_data["prompt"],
            duration_seconds=video_data.get("duration_seconds", 30),
        )

    for todo in todos:
        todo["status"] = "done"

    await notify(ws, "stage_update", {
        "name": "content_creator",
        "label": "Content creation",
        "status": "done",
        "todos": todos,
    })

    return {
        "content": content.model_dump(),
        "agent_traces": {
            **state.get("agent_traces", {}),
            "content_creator": {"todos": todos},
        },
    }
