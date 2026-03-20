"use client";

import {
  ResponsiveContainer, AreaChart, Area, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, Legend,
} from "recharts";
import { CHART_COLORS, CHART_GRID, CHART_AXIS } from "~/lib/chart-theme";
import { ChartTooltip } from "./ChartTooltip";
import type { TrendPoint, ForecastPoint } from "~/hooks/useTrends";

interface Props {
  points: TrendPoint[];
  forecasts: ForecastPoint[];
}

// Food type colors
const FOOD_COLORS: Record<string, string> = {
  small_game: "oklch(0.6 0.1 40)",
  mushrooms: "oklch(0.55 0.1 100)",
  herbs: "oklch(0.5 0.08 140)",
  berries: "oklch(0.55 0.15 340)",
  meat: "oklch(0.55 0.12 25)",
  bread: "oklch(0.65 0.1 80)",
  vegetables: "oklch(0.55 0.12 145)",
  fish: "oklch(0.6 0.1 230)",
  eggs: "oklch(0.65 0.08 85)",
};

export function ResourceTrendChart({ points, forecasts }: Props) {
  // Detect which food types have non-zero values
  const foodKeys = Object.keys(FOOD_COLORS).filter((key) =>
    points.some((p) => (p[key] as number) > 0)
  );

  // Merge points + forecasts
  const data = [
    ...points.map((p) => ({
      ...p,
      forecast_food: undefined as number | undefined,
    })),
    ...forecasts.map((f) => ({
      label: f.label,
      food_per_family: f.food_per_family,
      forecast_food: f.food_per_family,
    })),
  ];

  // Bridge last actual point to forecast
  if (points.length > 0 && forecasts.length > 0) {
    const last = data[points.length - 1] as Record<string, unknown>;
    last.forecast_food = last.food_per_family;
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid {...CHART_GRID} />
        <XAxis dataKey="label" {...CHART_AXIS} />
        <YAxis yAxisId="left" {...CHART_AXIS} />
        <YAxis yAxisId="right" orientation="right" {...CHART_AXIS} />
        <Tooltip content={<ChartTooltip />} />
        <Legend wrapperStyle={{ fontSize: 10, color: CHART_COLORS.muted }} />
        <ReferenceLine
          yAxisId="right"
          y={5}
          stroke={CHART_COLORS.red}
          strokeDasharray="5 5"
          label={{ value: "Danger", fill: CHART_COLORS.red, fontSize: 10 }}
        />
        {/* Stacked food breakdown */}
        {foodKeys.map((key, i) => (
          <Area
            key={key}
            yAxisId="left"
            type="monotone"
            dataKey={key}
            name={key.replace("_", " ")}
            stackId="food"
            fill={FOOD_COLORS[key]}
            fillOpacity={0.6}
            stroke={FOOD_COLORS[key]}
            strokeWidth={0}
          />
        ))}
        {/* Food per family line */}
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="food_per_family"
          name="food / family"
          stroke={CHART_COLORS.goldBright}
          strokeWidth={2}
          dot={{ r: 3, fill: CHART_COLORS.goldBright }}
        />
        {/* Forecast */}
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="forecast_food"
          name="forecast"
          stroke={CHART_COLORS.goldBright}
          strokeWidth={2}
          strokeDasharray="6 4"
          strokeOpacity={0.5}
          dot={false}
          legendType="none"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
