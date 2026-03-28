"use client";

import { useState } from "react";
import { ArrowRight, Sparkles } from "lucide-react";
import type { BrainstormPrompt, BrainstormQuestion, ProductBrief } from "@/lib/types";

interface Props {
  prompt: BrainstormPrompt;
  productBrief?: ProductBrief;
  onSubmit: (responses: Record<string, string>) => void;
}

export function BrainstormPanel({ prompt, productBrief, onSubmit }: Props) {
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [customValues, setCustomValues] = useState<Record<string, string>>({});

  const allAnswered = prompt.questions.every(
    (q) => responses[q.id] || customValues[q.id]
  );

  function handleSelect(questionId: string, value: string) {
    setResponses((prev) => ({ ...prev, [questionId]: value }));
    setCustomValues((prev) => ({ ...prev, [questionId]: "" }));
  }

  function handleCustom(questionId: string, value: string) {
    setCustomValues((prev) => ({ ...prev, [questionId]: value }));
    setResponses((prev) => ({ ...prev, [questionId]: "" }));
  }

  function handleSubmit() {
    const final: Record<string, string> = {};
    prompt.questions.forEach((q) => {
      final[q.id] = customValues[q.id] || responses[q.id] || "";
    });
    onSubmit(final);
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-12 space-y-8 animate-slide-up">
      {/* Product understood */}
      {productBrief && (
        <div className="border border-border rounded-xl p-5 bg-muted/20 space-y-2">
          <div className="flex items-center gap-2">
            <Sparkles size={13} className="text-orange-500" />
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              What we found
            </span>
          </div>
          <p className="text-sm font-medium">{productBrief.name}</p>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {prompt.product_understanding}
          </p>
          {productBrief.features.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-1">
              {productBrief.features.slice(0, 5).map((f) => (
                <span
                  key={f}
                  className="text-xs px-2.5 py-1 bg-white border border-border rounded-full text-muted-foreground"
                >
                  {f}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Questions */}
      <div className="space-y-7">
        <div className="space-y-1">
          <h2 className="text-xl font-semibold tracking-tight">
            A few quick questions
          </h2>
          <p className="text-sm text-muted-foreground">
            Help us nail the narrative. Pick an option or type your own.
          </p>
        </div>

        {prompt.questions.map((question, idx) => (
          <QuestionBlock
            key={question.id}
            question={question}
            index={idx + 1}
            selected={responses[question.id]}
            customValue={customValues[question.id] || ""}
            onSelect={(val) => handleSelect(question.id, val)}
            onCustom={(val) => handleCustom(question.id, val)}
          />
        ))}
      </div>

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={!allAnswered}
        className="flex items-center gap-2 px-6 py-3 bg-orange-500 text-white text-sm font-medium rounded-xl hover:bg-orange-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
      >
        Let&apos;s go
        <ArrowRight size={14} />
      </button>
    </div>
  );
}

interface QuestionBlockProps {
  question: BrainstormQuestion;
  index: number;
  selected?: string;
  customValue: string;
  onSelect: (val: string) => void;
  onCustom: (val: string) => void;
}

function QuestionBlock({
  question,
  index,
  selected,
  customValue,
  onSelect,
  onCustom,
}: QuestionBlockProps) {
  const isAnswered = selected || customValue;

  return (
    <div className="space-y-3">
      <div className="flex items-start gap-2">
        <span className="text-xs text-muted-foreground font-mono mt-0.5 w-4 shrink-0">
          {index}.
        </span>
        <p className="text-sm font-medium leading-relaxed">{question.question}</p>
      </div>

      {question.options && question.options.length > 0 && (
        <div className="ml-6 flex flex-wrap gap-2">
          {question.options.map((option) => (
            <button
              key={option}
              onClick={() => onSelect(option)}
              className={`px-3.5 py-2 rounded-xl text-sm border transition-all ${
                selected === option
                  ? "bg-orange-500 text-white border-orange-500"
                  : "bg-white border-border text-foreground hover:border-orange-300 hover:bg-orange-50/30"
              }`}
            >
              {option}
            </button>
          ))}
        </div>
      )}

      {/* Custom input — always available */}
      <div className="ml-6">
        <input
          type="text"
          placeholder={
            question.options?.length
              ? "Or type your own answer..."
              : "Your answer..."
          }
          value={customValue}
          onChange={(e) => onCustom(e.target.value)}
          className={`w-full px-4 py-2.5 rounded-xl border text-sm transition-all focus:outline-none focus:ring-2 focus:ring-orange-500/20 placeholder:text-muted-foreground/50 ${
            customValue
              ? "border-orange-400 bg-orange-50/20"
              : "border-border bg-white focus:border-orange-300"
          }`}
        />
      </div>

      {isAnswered && (
        <div className="ml-6">
          <span className="text-xs text-orange-500">✓ Got it</span>
        </div>
      )}
    </div>
  );
}
