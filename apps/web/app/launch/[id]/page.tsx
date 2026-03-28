"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { BrainstormPanel } from "@/components/chat/BrainstormPanel";
import { ReviewPanel } from "@/components/review/ReviewPanel";
import { AgentTrace } from "@/components/AgentTrace";
import { LiveFeed } from "@/components/LiveFeed";
import type { LaunchSession, AgentStage, StepOutput } from "@/lib/types";

type Phase = "loading" | "brainstorm" | "running" | "review" | "published";

export default function LaunchPage() {
  const { id } = useParams<{ id: string }>();
  const [phase, setPhase] = useState<Phase>("loading");
  const [session, setSession] = useState<LaunchSession>({
    id: id as string,
    status: "pending",
    created_at: new Date().toISOString(),
  });
  const [stages, setStages] = useState<AgentStage[]>([]);
  const [stepOutputs, setStepOutputs] = useState<StepOutput[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let cancelled = false;
    let ws: WebSocket | null = null;

    const timer = setTimeout(() => {
      if (cancelled) return;

      ws = new WebSocket(`ws://localhost:8000/ws/launch/${id}`);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        if (cancelled) return;
        const msg = JSON.parse(event.data);

        switch (msg.type) {
          case "session":
            setSession((prev) => ({ ...prev, ...msg.data }));
            break;
          case "phase":
            setPhase(msg.data as Phase);
            break;
          case "stage_update":
            setStages((prev) => {
              const idx = prev.findIndex((s) => s.name === msg.data.name);
              if (idx >= 0) {
                const updated = [...prev];
                updated[idx] = msg.data;
                return updated;
              }
              return [...prev, msg.data];
            });
            break;
          case "brainstorm_prompt":
            setPhase("brainstorm");
            setSession((prev) => ({ ...prev, brainstorm_prompt: msg.data }));
            break;
          case "step_output": {
            const key = `${msg.data.stage}-${msg.data.step}`;
            setStepOutputs((prev) => {
              const idx = prev.findIndex(
                (s) => `${s.stage}-${s.step}` === key
              );
              if (idx >= 0) {
                const updated = [...prev];
                updated[idx] = msg.data;
                return updated;
              }
              return [...prev, msg.data];
            });
            break;
          }
          case "content_ready":
            setPhase("review");
            setSession((prev) => ({ ...prev, content: msg.data }));
            break;
          case "error":
            console.error("[VibeLauncher] Server error:", msg.data);
            break;
        }
      };

      ws.onopen = () => {
        if (cancelled) {
          ws?.close();
          return;
        }
        ws!.send(JSON.stringify({ type: "init", launch_id: id }));
      };

      ws.onerror = (e) => {
        console.error("[VibeLauncher] WebSocket error:", e);
      };

      ws.onclose = () => {
        console.log("[VibeLauncher] WebSocket closed");
      };
    }, 100);

    return () => {
      cancelled = true;
      clearTimeout(timer);
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [id]);

  function sendBrainstormResponse(responses: Record<string, string>) {
    wsRef.current?.send(
      JSON.stringify({ type: "brainstorm_response", data: responses })
    );
    setStages((prev) => {
      const idx = prev.findIndex((s) => s.name === "human_brainstorm");
      if (idx >= 0) {
        const updated = [...prev];
        updated[idx] = {
          ...updated[idx],
          status: "done",
          todos: [
            { id: 1, task: "Generate brainstorm questions", status: "done" },
            { id: 2, task: "Your input received", status: "done" },
          ],
        };
        return updated;
      }
      return prev;
    });
    setPhase("running");
  }

  function sendContentApproval(approved: boolean, feedback?: string) {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "content_approval", approved, feedback }));
    } else {
      console.error("[VibeLauncher] Cannot send approval — WebSocket not open");
    }
  }

  const currentStageName =
    stages.find((s) => s.status === "running")?.label || "Working...";

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Nav */}
      <nav className="border-b border-border px-6 py-4 flex items-center justify-between">
        <span className="font-semibold text-sm tracking-tight">
          vibe<span className="text-gradient-orange">launcher</span>
        </span>
        <span className="text-xs text-muted-foreground">
          Launch session{" "}
          <span className="font-mono text-foreground">{id?.slice(0, 8)}</span>
        </span>
      </nav>

      <div className="flex flex-1 overflow-hidden">
        {/* Left: Agent trace */}
        <aside className="w-72 border-r border-border p-5 overflow-y-auto hidden lg:block">
          <AgentTrace stages={stages} currentPhase={phase} />
        </aside>

        {/* Main content area */}
        <main className="flex-1 overflow-y-auto">
          {phase === "loading" && (
            <div className="flex items-center justify-center h-full">
              <div className="space-y-4 text-center">
                <div className="w-8 h-8 border-2 border-orange-500/30 border-t-orange-500 rounded-full animate-spin mx-auto" />
                <p className="text-sm text-muted-foreground">
                  Analyzing your product...
                </p>
              </div>
            </div>
          )}

          {phase === "brainstorm" && session?.brainstorm_prompt && (
            <BrainstormPanel
              prompt={session.brainstorm_prompt}
              productBrief={session.product}
              onSubmit={sendBrainstormResponse}
            />
          )}

          {phase === "running" && (
            <LiveFeed
              steps={stepOutputs}
              currentStage={currentStageName}
              stages={stages}
            />
          )}

          {phase === "review" && session?.content && (
            <ReviewPanel
              content={session.content}
              strategy={session.strategy}
              onApprove={() => sendContentApproval(true)}
              onReject={(feedback) => sendContentApproval(false, feedback)}
            />
          )}

          {phase === "published" && (
            <div className="flex items-center justify-center h-full">
              <div className="space-y-4 text-center">
                <div className="w-12 h-12 rounded-full bg-orange-50 flex items-center justify-center mx-auto">
                  <span className="text-2xl">🚀</span>
                </div>
                <h2 className="text-xl font-semibold">You&apos;re live.</h2>
                <p className="text-sm text-muted-foreground">
                  Your launch has been posted to X.
                  <br />
                  Check back in an hour — engage with every reply.
                </p>
                {session?.published && (
                  <a
                    href={`https://x.com/i/web/status/${session.published.tweet_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-5 py-2.5 bg-black text-white text-sm rounded-xl hover:bg-zinc-800 transition-colors"
                  >
                    View on X →
                  </a>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
