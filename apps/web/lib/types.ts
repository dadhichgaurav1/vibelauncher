// Shared types between frontend and backend

export type AgentStageStatus = "pending" | "running" | "done" | "failed";

export interface TodoItem {
  id: number;
  task: string;
  status: "pending" | "in_progress" | "done" | "failed";
}

export interface AgentStage {
  name: string;
  label: string;
  status: AgentStageStatus;
  todos: TodoItem[];
  critique?: CritiqueResult;
}

export interface CritiqueResult {
  pass: boolean;
  score: number;
  issues: string[];
  suggestions: string[];
}

export interface ProductBrief {
  name: string;
  tagline: string;
  features: string[];
  target_audience_signals: string[];
  screenshots: string[];
  url?: string;
}

export interface BrainstormPrompt {
  product_understanding: string;
  questions: BrainstormQuestion[];
}

export interface BrainstormQuestion {
  id: string;
  question: string;
  options?: string[];
  allow_custom: true;
  type: "single" | "multi" | "text";
}

export interface ContentStrategy {
  formats: ContentFormat[];
  rationale: Record<ContentFormat, string | null>;
}

export type ContentFormat = "tweet" | "thread" | "image" | "video";

export interface LaunchStrategy {
  narrative: string;
  icp: string;
  tone: string;
  posting_day: string;
  posting_time: string;
  timezone: string;
  content_strategy: ContentStrategy;
  visual_brief: VisualBrief;
}

export interface VisualBrief {
  aesthetic: string;
  color_palette: string[];
  style: string;
  mood: string;
}

export interface ContentBundle {
  tweet?: TweetContent;
  thread?: ThreadContent;
  images?: ImageContent[];
  video?: VideoContent;
}

export interface TweetContent {
  text: string;
  char_count: number;
  first_reply?: string;
}

export interface ThreadContent {
  tweets: ThreadTweet[];
}

export interface ThreadTweet {
  position: number;
  text: string;
  char_count: number;
  media_suggestion?: string;
  is_hook: boolean;
  is_cta: boolean;
  is_engagement_trigger: boolean;
}

export interface ImageContent {
  url: string;
  prompt: string;
  dimensions: string;
}

export interface VideoContent {
  url: string;
  prompt: string;
  duration_seconds: number;
}

export interface PublishResult {
  tweet_id: string;
  thread_ids?: string[];
  scheduled_at?: string;
  posted_at?: string;
}

export interface LaunchSession {
  id: string;
  status: string;
  product?: ProductBrief;
  brainstorm_prompt?: BrainstormPrompt;
  strategy?: LaunchStrategy;
  content?: ContentBundle;
  published?: PublishResult;
  created_at: string;
}
