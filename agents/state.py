"""LangGraph shared state definition."""

from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class TodoItem(BaseModel):
    id: int
    task: str
    status: str = "pending"  # pending | in_progress | done | failed


class CritiqueResult(BaseModel):
    pass_: bool = Field(alias="pass")
    score: float  # 0-10
    issues: list[str]
    suggestions: list[str]

    class Config:
        populate_by_name = True


class AgentExecution(BaseModel):
    todos: list[TodoItem] = []
    completed_at: Optional[str] = None
    failed_todos: list[TodoItem] = []


class ProductBrief(BaseModel):
    name: str = ""
    tagline: str = ""
    features: list[str] = []
    target_audience_signals: list[str] = []
    screenshots: list[str] = []
    url: Optional[str] = None


class BrainstormQuestion(BaseModel):
    id: str
    question: str
    options: list[str] = []
    allow_custom: bool = True
    type: str = "single"  # single | multi | text


class BrainstormPrompt(BaseModel):
    product_understanding: str
    questions: list[BrainstormQuestion]


class VisualBrief(BaseModel):
    aesthetic: str = ""
    color_palette: list[str] = []
    style: str = ""
    mood: str = ""


class ContentStrategy(BaseModel):
    formats: list[str] = []  # tweet | thread | image | video
    rationale: dict[str, Optional[str]] = {}


class LaunchStrategy(BaseModel):
    narrative: str = ""
    icp: str = ""
    tone: str = ""
    posting_day: str = "Tuesday"
    posting_time: str = "9:00 AM"
    timezone: str = "ET"
    content_strategy: ContentStrategy = Field(default_factory=ContentStrategy)
    visual_brief: VisualBrief = Field(default_factory=VisualBrief)


class TweetContent(BaseModel):
    text: str
    char_count: int
    first_reply: Optional[str] = None


class ThreadTweet(BaseModel):
    position: int
    text: str
    char_count: int
    media_suggestion: Optional[str] = None
    is_hook: bool = False
    is_cta: bool = False
    is_engagement_trigger: bool = False


class ThreadContent(BaseModel):
    tweets: list[ThreadTweet]


class ImageContent(BaseModel):
    url: Optional[str] = None
    prompt: str
    dimensions: str = "1200x675"


class VideoContent(BaseModel):
    url: Optional[str] = None
    prompt: str
    duration_seconds: int = 30


class ContentBundle(BaseModel):
    tweet: Optional[TweetContent] = None
    thread: Optional[ThreadContent] = None
    images: Optional[list[ImageContent]] = None
    video: Optional[VideoContent] = None


class PublishResult(BaseModel):
    tweet_id: str = ""
    thread_ids: list[str] = []
    scheduled_at: Optional[str] = None
    posted_at: Optional[str] = None


class CritiqueBundle(BaseModel):
    product_brief: Optional[CritiqueResult] = None
    research_brief: Optional[CritiqueResult] = None
    strategy: Optional[CritiqueResult] = None
    content: Optional[dict[str, CritiqueResult]] = None


class VibeLaunchState(TypedDict):
    # Inputs — any combination
    launch_id: str
    user_id: str
    ws_channel: str
    input_url: Optional[str]
    input_markdown: Optional[str]
    input_transcript: Optional[str]
    input_readme: Optional[str]

    # Agent outputs (filled progressively)
    product: Optional[dict]          # ProductBrief serialized
    brainstorm_prompt: Optional[dict]  # BrainstormPrompt serialized
    brainstorm_responses: Optional[dict[str, str]]
    research_brief: Optional[dict]
    strategy: Optional[dict]         # LaunchStrategy serialized
    content: Optional[dict]          # ContentBundle serialized

    # Critic + retry tracking
    critiques: Optional[dict]
    retry_counts: dict[str, int]
    critic_feedback: Optional[str]

    # Agent execution traces
    agent_traces: dict[str, dict]

    # X OAuth
    x_access_token: Optional[str]
    x_access_token_secret: Optional[str]

    # Publishing
    approved: bool
    approval_feedback: Optional[str]
    selected_formats: Optional[list[str]]  # user-chosen formats to publish
    schedule_mode: Optional[str]            # "now" or "scheduled"
    published: Optional[dict]        # PublishResult serialized

    # Error
    error: Optional[str]
