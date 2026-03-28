"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Upload, Link, FileText, MessageSquare } from "lucide-react";

export default function HomePage() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [markdown, setMarkdown] = useState("");
  const [transcript, setTranscript] = useState("");
  const [activeTab, setActiveTab] = useState<"url" | "text" | "upload">("url");
  const [loading, setLoading] = useState(false);

  const hasInput = url.trim() || markdown.trim() || transcript.trim();

  async function handleLaunch() {
    if (!hasInput) return;
    setLoading(true);
    try {
      const res = await fetch("/api/agents/launch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: url || null,
          markdown: markdown || null,
          transcript: transcript || null,
        }),
      });
      const { launch_id } = await res.json();
      router.push(`/launch/${launch_id}`);
    } catch {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-white flex flex-col">
      {/* Nav */}
      <nav className="border-b border-border px-6 py-4 flex items-center justify-between">
        <span className="font-semibold text-sm tracking-tight">
          vibe<span className="text-gradient-orange">launcher</span>
        </span>
        <a
          href="/api/agents/auth/x"
          className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          Connect X account →
        </a>
      </nav>

      {/* Hero */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-24">
        <div className="max-w-2xl w-full space-y-10">
          <div className="space-y-4 text-center">
            <h1 className="text-5xl font-semibold tracking-tight leading-tight">
              Your app is built.
              <br />
              <span className="text-gradient-orange">Now launch it.</span>
            </h1>
            <p className="text-muted-foreground text-lg max-w-md mx-auto leading-relaxed">
              An agent team that turns your product into a full X launch —
              tweets, threads, images, video — and posts it for you.
            </p>
          </div>

          {/* Input card */}
          <div className="border border-border rounded-2xl overflow-hidden shadow-sm">
            {/* Tabs */}
            <div className="flex border-b border-border bg-muted/30">
              {[
                { id: "url", label: "Product URL", icon: Link },
                { id: "text", label: "Paste text", icon: FileText },
                { id: "upload", label: "Upload file", icon: Upload },
              ].map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setActiveTab(id as typeof activeTab)}
                  className={`flex items-center gap-2 px-5 py-3 text-sm transition-colors ${
                    activeTab === id
                      ? "text-foreground border-b-2 border-orange-500 bg-white"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Icon size={13} />
                  {label}
                </button>
              ))}
            </div>

            <div className="p-5 space-y-4 bg-white">
              {activeTab === "url" && (
                <div className="space-y-3">
                  <input
                    type="url"
                    placeholder="https://your-app.lovable.app"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-border text-sm focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-400 transition-all placeholder:text-muted-foreground/60"
                  />
                  <p className="text-xs text-muted-foreground">
                    We&apos;ll visit the URL and extract everything needed.
                  </p>
                </div>
              )}

              {activeTab === "text" && (
                <div className="space-y-3">
                  <textarea
                    placeholder="Paste your chat transcript, README, or product description..."
                    value={transcript || markdown}
                    onChange={(e) => setTranscript(e.target.value)}
                    rows={6}
                    className="w-full px-4 py-3 rounded-xl border border-border text-sm focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-400 transition-all placeholder:text-muted-foreground/60 resize-none font-mono"
                  />
                </div>
              )}

              {activeTab === "upload" && (
                <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-border rounded-xl cursor-pointer hover:border-orange-400 hover:bg-orange-50/30 transition-colors group">
                  <Upload
                    size={20}
                    className="text-muted-foreground group-hover:text-orange-500 transition-colors"
                  />
                  <span className="mt-2 text-sm text-muted-foreground group-hover:text-foreground transition-colors">
                    Drop your README or markdown file here
                  </span>
                  <input
                    type="file"
                    accept=".md,.txt,.pdf"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (!file) return;
                      const reader = new FileReader();
                      reader.onload = (ev) =>
                        setMarkdown(ev.target?.result as string);
                      reader.readAsText(file);
                    }}
                  />
                </label>
              )}

              {/* Optional extra fields */}
              {activeTab === "url" && (
                <details className="group">
                  <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground transition-colors flex items-center gap-1">
                    <MessageSquare size={11} />
                    Add chat transcript (optional but improves results)
                  </summary>
                  <textarea
                    placeholder="Paste your Lovable / Cursor / Replit chat transcript..."
                    value={transcript}
                    onChange={(e) => setTranscript(e.target.value)}
                    rows={4}
                    className="mt-3 w-full px-4 py-3 rounded-xl border border-border text-sm focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-400 transition-all placeholder:text-muted-foreground/60 resize-none font-mono"
                  />
                </details>
              )}

              <button
                onClick={handleLaunch}
                disabled={!hasInput || loading}
                className="w-full flex items-center justify-center gap-2 py-3 px-6 rounded-xl bg-orange-500 text-white text-sm font-medium hover:bg-orange-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all glow-orange"
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Analyzing your product...
                  </>
                ) : (
                  <>
                    Start launch
                    <ArrowRight size={14} />
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Social proof / positioning */}
          <p className="text-center text-xs text-muted-foreground">
            Built for solo builders on Lovable, Replit, Cursor, and beyond.
          </p>
        </div>
      </div>
    </main>
  );
}
