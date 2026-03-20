"use client";

import type { TrendPoint } from "~/hooks/useTrends";

interface Props {
  latest: TrendPoint | null;
}

interface Condition {
  label: string;
  met: boolean;
  detail: string;
}

export function SurplusAdvisor({ latest }: Props) {
  if (!latest) {
    return (
      <div className="text-sm text-muted-foreground italic p-4">
        No data available
      </div>
    );
  }

  const families = latest.families || 1;

  const conditions: Condition[] = [
    {
      label: "Food surplus",
      met: latest.food_per_family >= 15,
      detail: `${latest.food_per_family.toFixed(0)}/family (need 15)`,
    },
    {
      label: "Fuel secured",
      met: latest.firewood / families >= 10,
      detail: `${(latest.firewood / families).toFixed(0)}/family (need 10)`,
    },
    {
      label: "Approval stable",
      met: latest.approval >= 70,
      detail: `${latest.approval.toFixed(0)}% (need 70%)`,
    },
    {
      label: "Timber ready",
      met: latest.timber >= 15,
      detail: `${latest.timber.toFixed(0)} (need 15)`,
    },
    {
      label: "Stone available",
      met: (latest.rubblestone || 0) + (latest.stone || 0) >= 10,
      detail: `${((latest.rubblestone || 0) + (latest.stone || 0)).toFixed(0)} (need 10)`,
    },
    {
      label: "Tools stocked",
      met: (latest.tools || 0) >= 3,
      detail: `${(latest.tools || 0).toFixed(0)} (need 3)`,
    },
    {
      label: "No critical alerts",
      met: latest.alert_count === 0,
      detail: latest.alert_count > 0 ? `${latest.alert_count} active` : "Clear",
    },
  ];

  const metCount = conditions.filter((c) => c.met).length;
  const allMet = metCount === conditions.length;
  const criticalUnmet = metCount < 3;

  let verdict: string;
  let verdictColor: string;
  let verdictBg: string;

  if (allMet) {
    verdict = "Build Your Legacy";
    verdictColor = "text-[var(--color-ok-green-text)]";
    verdictBg = "bg-[var(--color-ok-green)]/10";
  } else if (criticalUnmet) {
    verdict = "Survival Mode";
    verdictColor = "text-destructive-foreground";
    verdictBg = "bg-destructive/10";
  } else {
    verdict = "Stabilise First";
    verdictColor = "text-[var(--color-gold-bright)]";
    verdictBg = "bg-[var(--color-gold-dim)]/10";
  }

  return (
    <div className="space-y-3">
      <div className={`text-center py-2 rounded-sm ${verdictBg}`}>
        <p className={`font-heading text-sm font-bold uppercase tracking-wider ${verdictColor}`}>
          {verdict}
        </p>
        <p className="text-xs text-muted-foreground mt-0.5">
          {metCount}/{conditions.length} conditions met
        </p>
      </div>
      <div className="space-y-1">
        {conditions.map((c) => (
          <div key={c.label} className="flex items-center gap-2 text-xs">
            <span className={c.met ? "text-[var(--color-ok-green-text)]" : "text-destructive-foreground"}>
              {c.met ? "\u2713" : "\u2717"}
            </span>
            <span className="text-foreground flex-1">{c.label}</span>
            <span className="text-muted-foreground">{c.detail}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
