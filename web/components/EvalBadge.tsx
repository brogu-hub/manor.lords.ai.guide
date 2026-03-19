"use client";

import { Badge } from "~/components/ui/badge";
import type { EvalResult } from "~/hooks/useSSE";

interface Props {
  evalResult: EvalResult | null;
}

function ScoreBadge({
  name,
  score,
  threshold,
}: {
  name: string;
  score: number;
  threshold: number;
}) {
  const passed = score >= threshold;
  const pct = Math.round(score * 100);

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-muted-foreground min-w-[70px]">
        {name}
      </span>
      <div className="flex-1 h-1.5 bg-secondary rounded-full overflow-hidden min-w-[60px]">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            passed
              ? "bg-[var(--color-ok-green)]"
              : "bg-[var(--color-alert-red)]"
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span
        className={`text-xs font-mono min-w-[32px] text-right ${
          passed
            ? "text-[var(--color-ok-green-text)]"
            : "text-[var(--color-alert-red-text)]"
        }`}
      >
        {pct}%
      </span>
    </div>
  );
}

const THRESHOLDS: Record<string, number> = {
  format: 0.7,
  specificity: 0.6,
  relevance: 0.6,
};

const LABELS: Record<string, string> = {
  format: "Format",
  specificity: "Specificity",
  relevance: "Relevance",
};

export function EvalBadge({ evalResult }: Props) {
  if (!evalResult || !evalResult.scores) return null;

  const passed = evalResult.passed;

  return (
    <div className="flex items-center gap-3">
      <Badge
        variant="outline"
        className={`text-xs font-heading uppercase tracking-wider border ${
          passed
            ? "border-[var(--color-ok-green)]/30 text-[var(--color-ok-green-text)] bg-[var(--color-ok-green)]/8"
            : "border-[var(--color-alert-red)]/30 text-[var(--color-alert-red-text)] bg-[var(--color-alert-red)]/8"
        }`}
      >
        {passed ? "Eval Pass" : `Eval Fail (attempt ${evalResult.attempt})`}
      </Badge>
      <div className="flex gap-4">
        {Object.entries(evalResult.scores).map(([key, score]) => (
          <ScoreBadge
            key={key}
            name={LABELS[key] ?? key}
            score={score}
            threshold={THRESHOLDS[key] ?? 0.6}
          />
        ))}
      </div>
    </div>
  );
}
