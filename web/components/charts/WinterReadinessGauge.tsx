"use client";

import type { TrendPoint } from "~/hooks/useTrends";

interface Props {
  latest: TrendPoint | null;
  season?: string;
}

function ReadinessBar({ label, ratio, detail }: { label: string; ratio: number; detail: string }) {
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
        <span className="font-heading text-foreground">{Math.round(pct)}% <span className="text-muted-foreground font-normal">({detail})</span></span>
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

  // Food: need ~8 per family to survive winter
  const foodPerFamily = latest.food_per_family || 0;
  const foodRatio = foodPerFamily / 8;

  // Fuel: need ~5 firewood per family
  const fwPerFamily = latest.firewood / families;
  const fuelRatio = fwPerFamily / 5;

  // Clothing: leather + pelts + hides available for processing
  const clothingMaterials = (latest.leather || 0) + (latest.pelts || 0) + (latest.hides || 0);
  const clothingRatio = clothingMaterials / (families * 2 || 1);

  // Construction: timber + tools for repairs
  const buildMaterials = (latest.timber || 0) + (latest.tools || 0);
  const buildRatio = buildMaterials / (families * 3 || 1);

  const composite = Math.round(
    ((Math.min(foodRatio, 1) * 0.35) +
     (Math.min(fuelRatio, 1) * 0.30) +
     (Math.min(clothingRatio, 1) * 0.20) +
     (Math.min(buildRatio, 1) * 0.15)) * 100
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
        <ReadinessBar
          label="Food"
          ratio={foodRatio}
          detail={`${foodPerFamily.toFixed(0)}/family`}
        />
        <ReadinessBar
          label="Fuel"
          ratio={fuelRatio}
          detail={`${fwPerFamily.toFixed(0)} fw/family`}
        />
        <ReadinessBar
          label="Clothing"
          ratio={clothingRatio}
          detail={`${clothingMaterials.toFixed(0)} materials`}
        />
        <ReadinessBar
          label="Materials"
          ratio={buildRatio}
          detail={`${buildMaterials.toFixed(0)} timber+tools`}
        />
      </div>
    </div>
  );
}
