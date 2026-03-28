"use client";

import { CheckCircle2, Circle, Loader2, XCircle, ChevronDown } from "lucide-react";
import { useState } from "react";
import type { AgentStage, TodoItem } from "@/lib/types";

const STAGE_ORDER = [
  { name: "product_analyst", label: "Product analysis" },
  { name: "human_brainstorm", label: "Brainstorm" },
  { name: "deep_research", label: "Deep research" },
  { name: "strategy", label: "Strategy" },
  { name: "content_creator", label: "Content creation" },
  { name: "media_generator", label: "Media generation" },
  { name: "publisher", label: "Publishing" },
];

interface Props {
  stages: AgentStage[];
  currentPhase: string;
}

export function AgentTrace({ stages, currentPhase }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);

  const stageMap = Object.fromEntries(stages.map((s) => [s.name, s]));

  return (
    <div className="space-y-1">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-4">
        Agent pipeline
      </p>
      {STAGE_ORDER.map(({ name, label }, i) => {
        const stage = stageMap[name];
        const status = stage?.status ?? (i === 0 ? "pending" : "pending");
        const isExpanded = expanded === name;

        return (
          <div key={name} className="space-y-0.5">
            <button
              onClick={() =>
                stage?.todos?.length
                  ? setExpanded(isExpanded ? null : name)
                  : undefined
              }
              className="w-full flex items-center gap-2.5 px-2 py-2 rounded-lg hover:bg-muted/50 transition-colors text-left group"
            >
              <StatusIcon status={status} />
              <span
                className={`text-sm flex-1 ${
                  status === "running"
                    ? "text-foreground font-medium"
                    : status === "done"
                    ? "text-foreground"
                    : "text-muted-foreground"
                }`}
              >
                {label}
              </span>
              {stage?.todos?.length ? (
                <ChevronDown
                  size={12}
                  className={`text-muted-foreground transition-transform ${
                    isExpanded ? "rotate-180" : ""
                  }`}
                />
              ) : null}
              {stage?.critique && !stage.critique.pass && (
                <span className="text-[10px] bg-orange-100 text-orange-600 px-1.5 py-0.5 rounded-full">
                  reviewing
                </span>
              )}
            </button>

            {/* Todos expansion */}
            {isExpanded && stage?.todos && (
              <div className="ml-7 space-y-1 pb-1">
                {stage.todos.map((todo) => (
                  <TodoRow key={todo.id} todo={todo} />
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case "done":
      return <CheckCircle2 size={14} className="text-orange-500 shrink-0" />;
    case "running":
      return (
        <Loader2 size={14} className="text-orange-500 animate-spin shrink-0" />
      );
    case "failed":
      return <XCircle size={14} className="text-red-400 shrink-0" />;
    default:
      return <Circle size={14} className="text-border shrink-0" />;
  }
}

function TodoRow({ todo }: { todo: TodoItem }) {
  return (
    <div className="flex items-start gap-2 py-0.5">
      <span className="mt-0.5 shrink-0">
        {todo.status === "done" ? (
          <CheckCircle2 size={11} className="text-orange-400" />
        ) : todo.status === "in_progress" ? (
          <Loader2 size={11} className="text-orange-400 animate-spin" />
        ) : todo.status === "failed" ? (
          <XCircle size={11} className="text-red-400" />
        ) : (
          <Circle size={11} className="text-border" />
        )}
      </span>
      <span
        className={`text-xs leading-relaxed ${
          todo.status === "done"
            ? "text-muted-foreground line-through"
            : todo.status === "in_progress"
            ? "text-foreground"
            : "text-muted-foreground"
        }`}
      >
        {todo.task}
      </span>
    </div>
  );
}
