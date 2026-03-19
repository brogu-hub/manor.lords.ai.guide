"use client";

import type { GamePath, SimilarState, TrendPoint } from "~/hooks/useTrends";

interface Props {
  gamePath: GamePath | null;
  similarStates: SimilarState[];
  latest: TrendPoint | null;
}

const VERDICT_STYLES: Record<string, { color: string; bg: string; arrow: string }> = {
  improving: { color: "text-[var(--color-ok-green-text)]", bg: "bg-[var(--color-ok-green)]/15", arrow: "\u2191" },
  stable: { color: "text-[var(--color-gold-bright)]", bg: "bg-[var(--color-gold-dim)]/15", arrow: "\u2192" },
  declining: { color: "text-[var(--color-gold-bright)]", bg: "bg-[var(--color-gold-dim)]/10", arrow: "\u2193" },
  critical: { color: "text-destructive-foreground", bg: "bg-destructive/10", arrow: "\u2193\u2193" },
};

const DIRECTION_ARROW: Record<string, string> = {
  rising: "\u2191",
  stable: "\u2192",
  falling: "\u2193",
};

const STATUS_COLOR: Record<string, string> = {
  good: "text-[var(--color-ok-green-text)]",
  warning: "text-[var(--color-gold-bright)]",
  critical: "text-destructive-foreground",
};

export function GamePathCard({ gamePath, similarStates, latest }: Props) {
  if (!gamePath) {
    return (
      <div className="text-sm text-muted-foreground italic p-4">
        Analyse saves to see your game path
      </div>
    );
  }

  const style = VERDICT_STYLES[gamePath.verdict] || VERDICT_STYLES.stable;

  // Count positive similar states
  const positiveCount = similarStates.filter((s) => s.label === "positive").length;
  const totalSimilar = similarStates.length;

  // Find worst factor for learning tip
  const worstFactor = gamePath.factors.reduce((worst, f) =>
    f.status === "critical" || (f.status === "warning" && worst.status !== "critical") ? f : worst
  , gamePath.factors[0]);

  return (
    <div className="space-y-3">
      {/* Verdict */}
      <div className={`text-center py-2 rounded-sm ${style.bg}`}>
        <div className="flex items-center justify-center gap-2">
          <span className={`text-xl ${style.color}`}>{style.arrow}</span>
          <span className={`font-heading text-sm font-bold uppercase tracking-wider ${style.color}`}>
            {gamePath.verdict}
          </span>
        </div>
        <p className="font-heading text-2xl font-bold text-foreground mt-1">
          {gamePath.score}
          <span className="text-xs text-muted-foreground font-normal">/100</span>
        </p>
      </div>

      {/* Factor breakdown */}
      <div className="space-y-1">
        {gamePath.factors.map((f) => (
          <div key={f.metric} className="flex items-center gap-1.5 text-xs">
            <span className={STATUS_COLOR[f.status] || "text-foreground"}>
              {DIRECTION_ARROW[f.direction] || "\u2192"}
            </span>
            <span className="text-foreground flex-1">{f.metric}</span>
            <span className="text-muted-foreground">{f.value}</span>
          </div>
        ))}
      </div>

      {/* Similar states comparison */}
      {totalSimilar > 0 && (
        <div className="border-t border-border pt-2">
          <p className="text-xs text-muted-foreground">
            <span className={positiveCount > totalSimilar / 2 ? "text-[var(--color-ok-green-text)]" : "text-destructive-foreground"}>
              {positiveCount} of {totalSimilar}
            </span>
            {" "}similar past states led to success
          </p>
          {similarStates[0]?.reasoning && (
            <p className="text-xs text-muted-foreground mt-1 italic leading-relaxed">
              {similarStates[0].reasoning.slice(0, 120)}
              {similarStates[0].reasoning.length > 120 ? "..." : ""}
            </p>
          )}
        </div>
      )}

      {/* Learning tip */}
      {worstFactor && worstFactor.status !== "good" && (
        <div className="border-t border-border pt-2">
          <p className="text-xs text-muted-foreground">
            <span className="text-primary font-semibold">Tip:</span>{" "}
            Focus on {worstFactor.metric.toLowerCase()} — currently at {worstFactor.value} and {worstFactor.direction}.
          </p>
        </div>
      )}
    </div>
  );
}
