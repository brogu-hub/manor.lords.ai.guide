"use client";

import type { TrendPoint } from "~/hooks/useTrends";

interface Props {
  latest: TrendPoint | null;
  season?: string;
}

function ReadinessBar({ label, ratio }: { label: string; ratio: number }) {
  const pct = Math.min(Math.max(ratio * 100, 0), 100);
  const color =
    pct >= 75
      ? "bg-[var(--color-ok-green)]"
      : pct >= 50
        ? "bg-[var(--color-gold-bright)]"
        : "bg-[var(--color-alert-red)]";

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-heading text-foreground">{Math.round(pct)}%</span>
      </div>
      <div className="h-2 bg-secondary rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function WinterReadinessGauge({ latest, season }: Props) {
  if (!latest) {
    return (
      <div className="text-sm text-muted-foreground italic p-4">
        No data available
      </div>
    );
  }

  const families = latest.families || 1;
  const foodRatio = latest.food_per_family / 8;
  const fuelRatio = latest.firewood / (families * 3);
  const clothingRatio = (latest.cloaks + latest.shoes) / (families * 2 || 1);

  const composite = Math.round(
    ((Math.min(foodRatio, 1) + Math.min(fuelRatio, 1) + Math.min(clothingRatio, 1)) / 3) * 100
  );

  const compositeColor =
    composite >= 75
      ? "text-[var(--color-ok-green-text)]"
      : composite >= 50
        ? "text-[var(--color-gold-bright)]"
        : "text-destructive-foreground";

  const currentSeason = season || latest.season || "";
  const label =
    currentSeason === "Winter"
      ? "Winter Survival"
      : currentSeason === "Spring"
        ? "Spring Recovery"
        : "Winter Preparedness";

  return (
    <div className="space-y-3">
      <div className="text-center">
        <span className={`font-heading text-2xl font-bold ${compositeColor}`}>
          {composite}%
        </span>
        <p className="text-xs text-muted-foreground mt-0.5">{label}</p>
      </div>
      <div className="space-y-2.5">
        <ReadinessBar label="Food" ratio={foodRatio} />
        <ReadinessBar label="Fuel" ratio={fuelRatio} />
        <ReadinessBar label="Clothing" ratio={clothingRatio} />
      </div>
    </div>
  );
}
