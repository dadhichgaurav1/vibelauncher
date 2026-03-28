"use client";

import { useState } from "react";
import { CheckCircle2, RefreshCw, Twitter, Clock, Eye } from "lucide-react";
import type { ContentBundle, LaunchStrategy } from "@/lib/types";

interface Props {
  content: ContentBundle;
  strategy?: LaunchStrategy;
  onApprove: () => void;
  onReject: (feedback: string) => void;
}

type Tab = "tweet" | "thread" | "images" | "video" | "strategy";

export function ReviewPanel({ content, strategy, onApprove, onReject }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>("tweet");
  const [rejecting, setRejecting] = useState(false);
  const [feedback, setFeedback] = useState("");

  const availableTabs: Tab[] = [
    ...(content.tweet ? (["tweet"] as Tab[]) : []),
    ...(content.thread ? (["thread"] as Tab[]) : []),
    ...(content.images?.length ? (["images"] as Tab[]) : []),
    ...(content.video ? (["video"] as Tab[]) : []),
    ...(strategy ? (["strategy"] as Tab[]) : []),
  ];

  return (
    <div className="max-w-3xl mx-auto px-6 py-10 space-y-6 animate-slide-up">
      <div className="space-y-1">
        <h2 className="text-xl font-semibold tracking-tight">Review your launch</h2>
        <p className="text-sm text-muted-foreground">
          Reviewed and polished by our critic agent. Make any edits, then approve.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-border">
        {availableTabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2.5 text-sm capitalize transition-colors ${
              activeTab === tab
                ? "text-foreground border-b-2 border-orange-500 font-medium"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="min-h-64">
        {activeTab === "tweet" && content.tweet && (
          <TweetPreview tweet={content.tweet} />
        )}
        {activeTab === "thread" && content.thread && (
          <ThreadPreview thread={content.thread} />
        )}
        {activeTab === "images" && content.images && (
          <ImagesPreview images={content.images} />
        )}
        {activeTab === "video" && content.video && (
          <VideoPreview video={content.video} />
        )}
        {activeTab === "strategy" && strategy && (
          <StrategyPreview strategy={strategy} />
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3 pt-2">
        {!rejecting ? (
          <>
            <button
              onClick={onApprove}
              className="flex items-center gap-2 px-6 py-3 bg-orange-500 text-white text-sm font-medium rounded-xl hover:bg-orange-600 transition-all"
            >
              <CheckCircle2 size={14} />
              Approve & post
            </button>
            <button
              onClick={() => setRejecting(true)}
              className="flex items-center gap-2 px-5 py-3 border border-border text-sm rounded-xl hover:bg-muted/40 transition-all text-muted-foreground hover:text-foreground"
            >
              <RefreshCw size={13} />
              Regenerate with notes
            </button>
          </>
        ) : (
          <div className="flex-1 space-y-3">
            <textarea
              placeholder="What should be different? Be specific: 'Make the hook more provocative' or 'The ICP is wrong — it's actually for designers, not developers'"
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              rows={3}
              autoFocus
              className="w-full px-4 py-3 rounded-xl border border-border text-sm focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-400 transition-all resize-none"
            />
            <div className="flex gap-2">
              <button
                onClick={() => {
                  if (feedback.trim()) onReject(feedback);
                  setRejecting(false);
                  setFeedback("");
                }}
                disabled={!feedback.trim()}
                className="px-5 py-2.5 bg-orange-500 text-white text-sm rounded-xl hover:bg-orange-600 disabled:opacity-40 transition-all"
              >
                Regenerate
              </button>
              <button
                onClick={() => setRejecting(false)}
                className="px-4 py-2.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function TweetPreview({ tweet }: { tweet: NonNullable<ContentBundle["tweet"]> }) {
  return (
    <div className="space-y-4">
      <div className="border border-border rounded-2xl p-5 space-y-3 bg-white shadow-sm">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center">
            <Twitter size={14} className="text-white" />
          </div>
          <div>
            <p className="text-sm font-medium">Your X Account</p>
            <p className="text-xs text-muted-foreground">@handle</p>
          </div>
        </div>
        <p className="text-sm leading-relaxed whitespace-pre-wrap">{tweet.text}</p>
        <div className="flex items-center justify-between text-xs text-muted-foreground pt-1">
          <span>{tweet.char_count}/280 characters</span>
        </div>
      </div>
      {tweet.first_reply && (
        <div className="ml-8 border border-dashed border-border rounded-2xl p-4 space-y-1">
          <p className="text-xs text-muted-foreground">First reply (with product link)</p>
          <p className="text-sm leading-relaxed whitespace-pre-wrap text-muted-foreground">
            {tweet.first_reply}
          </p>
        </div>
      )}
    </div>
  );
}

function ThreadPreview({ thread }: { thread: NonNullable<ContentBundle["thread"]> }) {
  return (
    <div className="space-y-2">
      {thread.tweets.map((tweet, i) => (
        <div
          key={i}
          className={`border rounded-2xl p-4 space-y-2 ${
            tweet.is_hook
              ? "border-orange-300 bg-orange-50/30"
              : "border-border bg-white"
          }`}
        >
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-muted-foreground">
              {i + 1}/{thread.tweets.length}
            </span>
            {tweet.is_hook && (
              <span className="text-xs bg-orange-100 text-orange-600 px-2 py-0.5 rounded-full">
                hook
              </span>
            )}
            {tweet.is_cta && (
              <span className="text-xs bg-black text-white px-2 py-0.5 rounded-full">
                CTA
              </span>
            )}
            {tweet.is_engagement_trigger && (
              <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">
                engagement trigger
              </span>
            )}
          </div>
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{tweet.text}</p>
          {tweet.media_suggestion && (
            <p className="text-xs text-muted-foreground italic">
              Media: {tweet.media_suggestion}
            </p>
          )}
          <p className="text-xs text-muted-foreground">{tweet.char_count}/280</p>
        </div>
      ))}
    </div>
  );
}

function ImagesPreview({ images }: { images: NonNullable<ContentBundle["images"]> }) {
  return (
    <div className="grid grid-cols-2 gap-4">
      {images.map((img, i) => (
        <div key={i} className="space-y-2">
          {img.url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={img.url}
              alt={`Generated image ${i + 1}`}
              className="w-full aspect-video object-cover rounded-xl border border-border"
            />
          ) : (
            <div className="w-full aspect-video bg-muted rounded-xl border border-border flex items-center justify-center">
              <Eye size={20} className="text-muted-foreground" />
            </div>
          )}
          <p className="text-xs text-muted-foreground leading-relaxed">{img.prompt}</p>
        </div>
      ))}
    </div>
  );
}

function VideoPreview({ video }: { video: NonNullable<ContentBundle["video"]> }) {
  return (
    <div className="space-y-3">
      {video.url ? (
        <video
          src={video.url}
          controls
          className="w-full aspect-video rounded-xl border border-border bg-black"
        />
      ) : (
        <div className="w-full aspect-video bg-muted rounded-xl border border-border flex items-center justify-center">
          <p className="text-sm text-muted-foreground">Generating video...</p>
        </div>
      )}
      <p className="text-xs text-muted-foreground">{video.duration_seconds}s · {video.prompt}</p>
    </div>
  );
}

function StrategyPreview({ strategy }: { strategy: LaunchStrategy }) {
  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-4">
        <div className="border border-border rounded-xl p-4 space-y-1">
          <p className="text-xs text-muted-foreground uppercase tracking-wider">Narrative</p>
          <p className="text-sm leading-relaxed">{strategy.narrative}</p>
        </div>
        <div className="border border-border rounded-xl p-4 space-y-1">
          <p className="text-xs text-muted-foreground uppercase tracking-wider">ICP</p>
          <p className="text-sm leading-relaxed">{strategy.icp}</p>
        </div>
        <div className="border border-border rounded-xl p-4 space-y-1">
          <p className="text-xs text-muted-foreground uppercase tracking-wider">Tone</p>
          <p className="text-sm">{strategy.tone}</p>
        </div>
        <div className="border border-border rounded-xl p-4 space-y-1 flex items-start gap-2">
          <Clock size={13} className="text-muted-foreground mt-0.5 shrink-0" />
          <div>
            <p className="text-xs text-muted-foreground uppercase tracking-wider">Post timing</p>
            <p className="text-sm">
              {strategy.posting_day} · {strategy.posting_time} {strategy.timezone}
            </p>
          </div>
        </div>
      </div>
      <div className="border border-border rounded-xl p-4 space-y-3">
        <p className="text-xs text-muted-foreground uppercase tracking-wider">Format decisions</p>
        {Object.entries(strategy.content_strategy.rationale)
          .filter(([, reason]) => reason)
          .map(([format, reason]) => (
            <div key={format} className="flex gap-2">
              <span className="text-xs font-mono text-orange-500 w-16 shrink-0">{format}</span>
              <span className="text-xs text-muted-foreground leading-relaxed">{reason}</span>
            </div>
          ))}
      </div>
    </div>
  );
}
