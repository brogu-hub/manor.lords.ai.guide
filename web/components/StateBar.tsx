"use client";

import { useState } from "react";
import { Card } from "~/components/ui/card";
import type { GameState } from "~/hooks/useSSE";

interface Props {
  state: GameState | null;
}

type ValueStatus = "normal" | "warning" | "critical" | "good";

function StatItem({
  label,
  value,
  status = "normal",
  small,
}: {
  label: string;
  value: string | number;
  status?: ValueStatus;
  small?: boolean;
}) {
  const colorClass = {
    normal: "text-primary",
    good: "text-[var(--color-ok-green-text)]",
    warning: "text-[var(--color-gold-bright)]",
    critical: "text-destructive-foreground",
  }[status];

  return (
    <Card
      className={`flex-1 px-3 py-2 text-center bg-card border-border ${
        small ? "min-w-[72px]" : "min-w-[90px]"
      }`}
    >
      <span className="block font-heading text-[0.6rem] text-muted-foreground uppercase tracking-widest leading-tight">
        {label}
      </span>
      <span
        className={`block font-heading font-bold ${colorClass} ${
          small ? "text-base" : "text-lg"
        }`}
      >
        {value}
      </span>
    </Card>
  );
}

function ResourceGroup({
  title,
  items,
}: {
  title: string;
  items: { label: string; value: number; status?: ValueStatus }[];
}) {
  const hasValues = items.some((i) => i.value > 0);
  if (!hasValues && items.every((i) => i.value === 0)) return null;

  return (
    <div>
      <p className="text-[0.6rem] font-heading text-muted-foreground uppercase tracking-widest mb-1 px-1">
        {title}
      </p>
      <div className="flex gap-1 flex-wrap">
        {items.map((item) => (
          <StatItem
            key={item.label}
            label={item.label}
            value={Math.round(item.value)}
            status={item.status}
            small
          />
        ))}
      </div>
    </div>
  );
}

function getStatus(
  value: number,
  warning: number,
  critical: number,
): ValueStatus {
  if (value <= critical) return "critical";
  if (value <= warning) return "warning";
  return "normal";
}

export function StateBar({ state }: Props) {
  const [expanded, setExpanded] = useState(false);

  if (!state) return null;

  const meta = state.meta ?? {};
  const pop = state.settlement?.population ?? {};
  const food = state.resources?.food;
  const fuel = state.resources?.fuel;
  const construction = state.resources?.construction;
  const clothing = state.resources?.clothing;
  const production = state.resources?.production;
  const military = state.military;
  const approval = state.settlement?.approval;
  const alerts = state.alerts ?? [];

  const foodTotal =
    typeof food?.total === "number" ? Math.round(food.total) : "-";
  const approvalVal =
    typeof approval === "number" ? `${Math.round(approval)}%` : "-";
  const firewood =
    typeof fuel?.firewood === "number" ? Math.round(fuel.firewood) : "-";
  const timber =
    typeof construction?.timber === "number" ? Math.round(construction.timber) : "-";
  const rubblestone =
    typeof construction?.rubblestone === "number" ? Math.round(construction.rubblestone) : "-";

  return (
    <div className="col-span-full space-y-2">
      {/* Primary stats row */}
      <div className="flex gap-1.5 flex-wrap">
        {meta.game_version && (
          <StatItem label="Version" value={meta.game_version.replace("Version ", "")} small />
        )}
        <StatItem label="Year" value={meta.year ?? "-"} />
        <StatItem label="Season" value={meta.season ?? "-"} />
        <StatItem label="Families" value={pop.families ?? "-"} />
        <StatItem
          label="Food"
          value={foodTotal}
          status={
            typeof foodTotal === "number"
              ? getStatus(foodTotal, 30, 10)
              : "normal"
          }
        />
        <StatItem
          label="Firewood"
          value={firewood}
          status={
            typeof firewood === "number"
              ? getStatus(firewood, 15, 5)
              : "normal"
          }
        />
        <StatItem
          label="Timber"
          value={timber}
          status={
            typeof timber === "number"
              ? getStatus(timber, 10, 3)
              : "normal"
          }
        />
        <StatItem
          label="Stone"
          value={rubblestone}
        />
        <StatItem
          label="Approval"
          value={approvalVal}
          status={
            typeof approval === "number"
              ? approval >= 70
                ? "good"
                : getStatus(approval, 50, 30)
              : "normal"
          }
        />
        <StatItem
          label="Alerts"
          value={alerts.length}
          status={alerts.length > 0 ? "critical" : "good"}
        />

        {/* Expand toggle */}
        <button
          onClick={() => setExpanded((v) => !v)}
          className="flex-none flex items-center justify-center min-w-[36px] px-2 py-2 bg-card border border-border rounded-[var(--radius)] text-muted-foreground hover:text-foreground hover:border-ring transition-colors"
          title={expanded ? "Show less" : "Show all resources"}
        >
          <svg
            viewBox="0 0 24 24"
            width="14"
            height="14"
            fill="currentColor"
            className={`transition-transform ${expanded ? "rotate-180" : ""}`}
          >
            <path d="M7 10l5 5 5-5z" />
          </svg>
        </button>
      </div>

      {/* Expanded resource details */}
      {expanded && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-3 bg-card border border-border rounded-[var(--radius)]">
          <ResourceGroup
            title="Food"
            items={[
              { label: "Small Game", value: food?.small_game ?? 0 },
              { label: "Mushrooms", value: food?.mushrooms ?? 0 },
              { label: "Herbs", value: food?.herbs ?? 0 },
              { label: "Berries", value: food?.berries ?? 0 },
              { label: "Meat", value: food?.meat ?? 0 },
              { label: "Bread", value: food?.bread ?? 0 },
              { label: "Vegs", value: food?.vegetables ?? 0 },
              { label: "Eggs", value: food?.eggs ?? 0 },
              { label: "Fish", value: food?.fish ?? 0 },
              { label: "Grain", value: food?.grain ?? 0 },
            ]}
          />
          <ResourceGroup
            title="Construction"
            items={[
              { label: "Timber", value: construction?.timber ?? 0 },
              { label: "Planks", value: construction?.planks ?? 0 },
              { label: "Rubblestone", value: construction?.rubblestone ?? 0 },
              { label: "Stone", value: construction?.stone ?? 0 },
              { label: "Clay", value: construction?.clay ?? 0 },
              { label: "Tools", value: construction?.tools ?? 0 },
            ]}
          />
          <ResourceGroup
            title="Clothing"
            items={[
              { label: "Pelts", value: clothing?.pelts ?? 0 },
              { label: "Hides", value: clothing?.hides ?? 0 },
              { label: "Leather", value: clothing?.leather ?? 0 },
              { label: "Yarn", value: clothing?.yarn ?? 0 },
              { label: "Shoes", value: clothing?.shoes ?? 0 },
              { label: "Cloaks", value: clothing?.cloaks ?? 0 },
            ]}
          />
          <ResourceGroup
            title="Production"
            items={[
              { label: "Iron Ore", value: production?.iron_ore ?? 0 },
              { label: "Iron", value: production?.iron ?? 0 },
              { label: "Ale", value: production?.ale ?? 0 },
              { label: "Malt", value: production?.malt ?? 0 },
              { label: "Flour", value: production?.flour ?? 0 },
              { label: "Tools", value: production?.tools ?? 0 },
            ]}
          />

          {/* Settlement details */}
          <ResourceGroup
            title="Settlement"
            items={[
              { label: "Workers", value: pop.workers ?? 0 },
              {
                label: "Homeless",
                value: pop.homeless ?? 0,
                status: (pop.homeless ?? 0) > 0 ? "warning" : "normal",
              },
              {
                label: "Wealth",
                value: state.settlement?.regional_wealth ?? 0,
              },
              { label: "Dev Pts", value: state.development_points ?? 0 },
            ]}
          />

          {/* Fuel */}
          <ResourceGroup
            title="Fuel"
            items={[
              {
                label: "Firewood",
                value: fuel?.firewood ?? 0,
                status:
                  typeof fuel?.firewood === "number"
                    ? getStatus(fuel.firewood, 15, 5)
                    : "normal",
              },
              { label: "Charcoal", value: fuel?.charcoal ?? 0 },
            ]}
          />

          {/* Military */}
          {military && (
            <ResourceGroup
              title="Military"
              items={[
                { label: "Retinue", value: military.retinue_count ?? 0 },
                {
                  label: "Bandits",
                  value: military.bandit_camps_nearby ?? 0,
                  status:
                    (military.bandit_camps_nearby ?? 0) > 0
                      ? "warning"
                      : "normal",
                },
              ]}
            />
          )}
        </div>
      )}
    </div>
  );
}
