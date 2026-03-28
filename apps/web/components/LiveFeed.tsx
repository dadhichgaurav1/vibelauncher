"use client";

import { useEffect, useRef } from "react";
import {
  Search,
  Target,
  TrendingUp,
  Users,
  Calendar,
  Palette,
  Layout,
  Twitter,
  Image as ImageIcon,
  Video,
  Clock,
  Loader2,
} from "lucide-react";
import type { StepOutput, AgentStage } from "@/lib/types";

interface Props {
  steps: StepOutput[];
  currentStage: string;
  stages: AgentStage[];
}

export function LiveFeed({ steps, currentStage, stages }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [steps.length]);

  return (
    <div className="max-w-2xl mx-auto px-6 py-8">
      {/* Status bar */}
      <div className="flex items-center gap-3 pb-5 mb-6 border-b border-border">
        <div className="w-4 h-4 border-2 border-orange-500/30 border-t-orange-500 rounded-full animate-spin shrink-0" />
        <p className="text-sm font-medium">{currentStage}</p>
        <span className="text-xs text-muted-foreground ml-auto">
          {steps.length} {steps.length === 1 ? "insight" : "insights"} found
        </span>
      </div>

      {/* Live cards */}
      {steps.length === 0 ? (
        <div className="text-center py-16 space-y-3">
          <Search size={20} className="text-muted-foreground mx-auto" />
          <p className="text-sm text-muted-foreground">
            Researching your niche on X...
          </p>
          <p className="text-xs text-muted-foreground">
            Results will appear here as they&apos;re discovered.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {steps.map((step) => (
            <div
              key={`${step.stage}-${step.step}`}
              className="animate-slide-up"
            >
              <StepCard step={step} />
            </div>
          ))}
        </div>
      )}

      {/* Mobile sidebar */}
      <div className="lg:hidden mt-8 pt-6 border-t border-border">
        <p className="text-xs text-muted-foreground uppercase tracking-wider mb-3">
          Pipeline
        </p>
        {stages.map((s) => (
          <div key={s.name} className="flex items-center gap-2 py-1">
            {s.status === "running" ? (
              <Loader2 size={12} className="text-orange-500 animate-spin" />
            ) : s.status === "done" ? (
              <div className="w-3 h-3 rounded-full bg-orange-500" />
            ) : (
              <div className="w-3 h-3 rounded-full bg-border" />
            )}
            <span className="text-xs text-muted-foreground">{s.label}</span>
          </div>
        ))}
      </div>

      <div ref={bottomRef} />
    </div>
  );
}

function StepCard({ step }: { step: StepOutput }) {
  const stageIcons: Record<string, typeof Search> = {
    product_analyst: Target,
    deep_research: Search,
    strategy: Layout,
    content_creator: Twitter,
    media_generator: ImageIcon,
  };
  const Icon = stageIcons[step.stage] || Search;

  const stageColors: Record<string, string> = {
    product_analyst: "text-blue-600 bg-blue-50",
    deep_research: "text-purple-600 bg-purple-50",
    strategy: "text-orange-600 bg-orange-50",
    content_creator: "text-black bg-zinc-100",
    media_generator: "text-emerald-600 bg-emerald-50",
  };
  const colorClass = stageColors[step.stage] || "text-muted-foreground bg-muted";

  return (
    <div className="border border-border rounded-xl overflow-hidden bg-white">
      {/* Card header */}
      <div className="flex items-center gap-2 px-4 py-2.5 bg-muted/20 border-b border-border">
        <div className={`w-5 h-5 rounded flex items-center justify-center ${colorClass}`}>
          <Icon size={11} />
        </div>
        <span className="text-xs font-medium text-foreground">
          {step.label}
        </span>
        <span className="text-[10px] text-muted-foreground ml-auto uppercase tracking-wider">
          {step.stage.replace("_", " ")}
        </span>
      </div>

      {/* Card body */}
      <div className="px-4 py-3">
        <StepBody step={step} />
      </div>
    </div>
  );
}

function StepBody({ step }: { step: StepOutput }) {
  const { stage, step: stepKey, data } = step;

  // ─── Deep Research cards ────────────────────────────────────────────
  if (stage === "deep_research") {
    if (stepKey === "icp" && data) {
      return (
        <div className="space-y-2.5">
          <p className="text-sm leading-relaxed">{data.description}</p>
          {data.pain_points?.length > 0 && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Pain points</p>
              <div className="flex flex-wrap gap-1.5">
                {data.pain_points.map((p: string, i: number) => (
                  <span key={i} className="text-xs px-2 py-1 bg-red-50 text-red-700 rounded-md">{p}</span>
                ))}
              </div>
            </div>
          )}
          {data.desires?.length > 0 && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Desires</p>
              <div className="flex flex-wrap gap-1.5">
                {data.desires.map((d: string, i: number) => (
                  <span key={i} className="text-xs px-2 py-1 bg-green-50 text-green-700 rounded-md">{d}</span>
                ))}
              </div>
            </div>
          )}
          {data.x_behavior && (
            <p className="text-xs text-muted-foreground italic">{data.x_behavior}</p>
          )}
        </div>
      );
    }

    if (stepKey === "narrative_angles" && Array.isArray(data)) {
      return (
        <div className="space-y-3">
          {data.slice(0, 4).map((angle: { angle: string; hook_example: string; why_it_works: string }, i: number) => (
            <div key={i} className="space-y-1">
              <div className="flex items-start gap-2">
                <span className="text-xs font-mono text-orange-500 mt-0.5 shrink-0">{i + 1}.</span>
                <div className="space-y-1">
                  <p className="text-sm font-medium">{angle.angle}</p>
                  <p className="text-xs font-mono text-muted-foreground bg-muted/50 px-2 py-1 rounded">
                    &ldquo;{angle.hook_example}&rdquo;
                  </p>
                  <p className="text-xs text-muted-foreground">{angle.why_it_works}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      );
    }

    if (stepKey === "competitor_analysis" && Array.isArray(data)) {
      return (
        <div className="grid grid-cols-1 gap-2">
          {data.slice(0, 4).map((c: { account: string; what_works: string; engagement_pattern: string }, i: number) => (
            <div key={i} className="flex gap-3 p-2.5 bg-muted/20 rounded-lg">
              <div className="w-7 h-7 rounded-full bg-zinc-200 flex items-center justify-center shrink-0">
                <Users size={12} className="text-zinc-600" />
              </div>
              <div className="space-y-0.5 min-w-0">
                <p className="text-xs font-medium truncate">{c.account}</p>
                <p className="text-xs text-muted-foreground">{c.what_works}</p>
              </div>
            </div>
          ))}
        </div>
      );
    }

    if (stepKey === "viral_patterns" && data) {
      return (
        <div className="space-y-2">
          {data.hook_styles?.length > 0 && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Hook styles that work</p>
              <div className="flex flex-wrap gap-1.5">
                {data.hook_styles.map((h: string, i: number) => (
                  <span key={i} className="text-xs px-2 py-1 bg-purple-50 text-purple-700 rounded-md">{h}</span>
                ))}
              </div>
            </div>
          )}
          {data.engagement_triggers?.length > 0 && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Engagement triggers</p>
              <div className="flex flex-wrap gap-1.5">
                {data.engagement_triggers.map((t: string, i: number) => (
                  <span key={i} className="text-xs px-2 py-1 bg-orange-50 text-orange-700 rounded-md">{t}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      );
    }

    if (stepKey === "content_strategy" && data) {
      return (
        <div className="space-y-2">
          <div className="flex flex-wrap gap-2">
            {data.formats?.map((f: string) => (
              <span key={f} className="text-xs px-2.5 py-1 bg-black text-white rounded-full font-medium">{f}</span>
            ))}
          </div>
          {data.rationale && Object.entries(data.rationale).filter(([, v]) => v).map(([k, v]) => (
            <div key={k} className="flex gap-2">
              <span className="text-xs font-mono text-orange-500 w-12 shrink-0">{k}</span>
              <span className="text-xs text-muted-foreground">{v as string}</span>
            </div>
          ))}
        </div>
      );
    }

    if (stepKey === "optimal_timing" && data) {
      return (
        <div className="flex items-center gap-3">
          <Calendar size={14} className="text-orange-500 shrink-0" />
          <div>
            <p className="text-sm font-medium">{data.day} · {data.time} {data.timezone}</p>
            <p className="text-xs text-muted-foreground">{data.reasoning}</p>
          </div>
        </div>
      );
    }
  }

  // ─── Strategy cards ─────────────────────────────────────────────────
  if (stage === "strategy") {
    if (stepKey === "narrative") {
      return (
        <div className="space-y-3">
          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Narrative</p>
            <p className="text-sm leading-relaxed">{data.narrative}</p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">ICP</p>
              <p className="text-xs leading-relaxed">{data.icp}</p>
            </div>
            <div className="space-y-1">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Tone</p>
              <p className="text-xs leading-relaxed">{data.tone}</p>
            </div>
          </div>
        </div>
      );
    }
    if (stepKey === "schedule") {
      return (
        <div className="flex items-center gap-3">
          <Clock size={14} className="text-orange-500 shrink-0" />
          <p className="text-sm">{data.day} · {data.time} {data.tz}</p>
        </div>
      );
    }
    if (stepKey === "format_decisions") {
      return (
        <div className="space-y-2">
          <div className="flex flex-wrap gap-2">
            {data?.formats?.map((f: string) => (
              <span key={f} className="text-xs px-2.5 py-1 bg-orange-500 text-white rounded-full font-medium">{f}</span>
            ))}
          </div>
          {data?.rationale && Object.entries(data.rationale).filter(([, v]) => v).map(([k, v]) => (
            <div key={k} className="flex gap-2">
              <span className="text-xs font-mono text-orange-500 w-12 shrink-0">{k}</span>
              <span className="text-xs text-muted-foreground">{v as string}</span>
            </div>
          ))}
        </div>
      );
    }
    if (stepKey === "visual_brief") {
      return (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Palette size={13} className="text-orange-500" />
            <span className="text-sm">{data.aesthetic}</span>
          </div>
          {data.color_palette?.length > 0 && (
            <div className="flex gap-1.5">
              {data.color_palette.map((c: string, i: number) => (
                <div
                  key={i}
                  className="w-6 h-6 rounded-md border border-border"
                  style={{ background: c }}
                  title={c}
                />
              ))}
            </div>
          )}
          <p className="text-xs text-muted-foreground">{data.style} · {data.mood}</p>
        </div>
      );
    }
  }

  // ─── Content preview cards ──────────────────────────────────────────
  if (stage === "content_creator") {
    if (stepKey === "tweet_preview" && data) {
      return (
        <div className="space-y-2">
          {/* Mock tweet */}
          <div className="bg-zinc-950 text-white rounded-xl p-4 space-y-2">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-400 to-orange-600" />
              <div>
                <p className="text-xs font-medium text-white">Your Account</p>
                <p className="text-[10px] text-zinc-400">@handle</p>
              </div>
            </div>
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{data.text}</p>
            <p className="text-[10px] text-zinc-500">{data.char_count || data.text?.length}/280</p>
          </div>
          {data.first_reply && (
            <div className="ml-6 border-l-2 border-orange-200 pl-3">
              <p className="text-[10px] text-muted-foreground mb-1">First reply (with product link)</p>
              <p className="text-xs text-muted-foreground">{data.first_reply}</p>
            </div>
          )}
        </div>
      );
    }

    if (stepKey === "thread_preview" && data?.tweets) {
      return (
        <div className="space-y-1.5">
          {data.tweets.slice(0, 5).map((tweet: { position: number; text: string; char_count: number; is_hook?: boolean; is_cta?: boolean; is_engagement_trigger?: boolean }, i: number) => (
            <div
              key={i}
              className={`rounded-lg p-3 text-sm space-y-1 ${
                tweet.is_hook
                  ? "bg-orange-50 border border-orange-200"
                  : "bg-muted/30 border border-border"
              }`}
            >
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] font-mono text-muted-foreground">
                  {tweet.position}/{data.tweets.length}
                </span>
                {tweet.is_hook && (
                  <span className="text-[10px] bg-orange-500 text-white px-1.5 py-0.5 rounded-full">hook</span>
                )}
                {tweet.is_cta && (
                  <span className="text-[10px] bg-black text-white px-1.5 py-0.5 rounded-full">CTA</span>
                )}
                {tweet.is_engagement_trigger && (
                  <span className="text-[10px] bg-blue-500 text-white px-1.5 py-0.5 rounded-full">engage</span>
                )}
              </div>
              <p className="text-xs leading-relaxed whitespace-pre-wrap">{tweet.text}</p>
            </div>
          ))}
          {data.tweets.length > 5 && (
            <p className="text-xs text-muted-foreground text-center">
              + {data.tweets.length - 5} more tweets
            </p>
          )}
        </div>
      );
    }

    if (stepKey === "image_prompts" && Array.isArray(data)) {
      return (
        <div className="space-y-2">
          {data.map((img: { prompt: string; dimensions?: string; placement?: string }, i: number) => (
            <div key={i} className="flex gap-3 p-2.5 bg-muted/20 rounded-lg">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-orange-100 to-orange-200 flex items-center justify-center shrink-0">
                <ImageIcon size={14} className="text-orange-600" />
              </div>
              <div className="space-y-0.5 min-w-0">
                <p className="text-xs leading-relaxed">{img.prompt}</p>
                {img.placement && (
                  <p className="text-[10px] text-muted-foreground">Placement: {img.placement}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      );
    }

    if (stepKey === "video_prompt") {
      return (
        <div className="flex gap-3 p-2.5 bg-muted/20 rounded-lg">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-100 to-purple-200 flex items-center justify-center shrink-0">
            <Video size={14} className="text-purple-600" />
          </div>
          <div className="space-y-0.5">
            <p className="text-xs leading-relaxed">{data.prompt}</p>
            <p className="text-[10px] text-muted-foreground">{data.duration_seconds}s · {data.aspect_ratio}</p>
          </div>
        </div>
      );
    }
  }

  // ─── Media generation cards ─────────────────────────────────────────
  if (stage === "media_generator") {
    if (step.type === "image") {
      return (
        <div className="space-y-2">
          {data.url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={data.url}
              alt={data.prompt}
              className="w-full aspect-video object-cover rounded-lg border border-border"
            />
          ) : (
            <div className="w-full aspect-video bg-muted rounded-lg border border-border flex items-center justify-center">
              <Loader2 size={16} className="text-muted-foreground animate-spin" />
            </div>
          )}
          <p className="text-xs text-muted-foreground">{data.prompt}</p>
        </div>
      );
    }
    if (step.type === "status") {
      return (
        <div className="flex items-center gap-3">
          {data.status === "generating" ? (
            <Loader2 size={14} className="text-purple-500 animate-spin shrink-0" />
          ) : (
            <Video size={14} className="text-green-500 shrink-0" />
          )}
          <div>
            <p className="text-sm font-medium">
              {data.status === "generating" ? "Generating video..." : "Video ready"}
            </p>
            <p className="text-xs text-muted-foreground">{data.prompt}</p>
          </div>
        </div>
      );
    }
  }

  // ─── Product brief card ─────────────────────────────────────────────
  if (stage === "product_analyst" && stepKey === "product_brief") {
    return (
      <div className="space-y-2">
        <p className="text-sm font-medium">{data.name}</p>
        <p className="text-xs text-muted-foreground">{data.tagline}</p>
        {data.features?.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {data.features.slice(0, 5).map((f: string, i: number) => (
              <span key={i} className="text-xs px-2 py-1 bg-muted rounded-md">{f}</span>
            ))}
          </div>
        )}
      </div>
    );
  }

  // ─── Fallback: render data as formatted text ────────────────────────
  if (typeof data === "string") {
    return <p className="text-sm leading-relaxed">{data}</p>;
  }

  if (typeof data === "object" && data !== null) {
    return (
      <div className="space-y-1">
        {Object.entries(data).map(([k, v]) => (
          <div key={k} className="flex gap-2">
            <span className="text-xs font-mono text-muted-foreground w-28 shrink-0">{k}</span>
            <span className="text-xs text-foreground">
              {typeof v === "string" ? v : JSON.stringify(v)}
            </span>
          </div>
        ))}
      </div>
    );
  }

  return <p className="text-xs text-muted-foreground">No data</p>;
}
