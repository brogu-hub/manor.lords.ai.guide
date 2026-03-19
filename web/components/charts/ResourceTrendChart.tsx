"use client";

import {
  ResponsiveContainer, AreaChart, Area, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine,
} from "recharts";
import { CHART_COLORS, CHART_GRID, CHART_AXIS } from "~/lib/chart-theme";
import { ChartTooltip } from "./ChartTooltip";
import type { TrendPoint, ForecastPoint } from "~/hooks/useTrends";

interface Props {
  points: TrendPoint[];
  forecasts: ForecastPoint[];
}

export function ResourceTrendChart({ points, forecasts }: Props) {
  // Merge points + forecasts for continuous line
  const data = [
    ...points.map((p) => ({
      label: p.label,
      food_total: p.food_total,
      food_per_family: p.food_per_family,
      forecast_food: undefined as number | undefined,
    })),
    ...forecasts.map((f) => ({
      label: f.label,
      food_total: undefined as number | undefined,
      food_per_family: undefined as number | undefined,
      forecast_food: f.food_per_family,
    })),
  ];

  // Bridge: last actual point connects to forecast
  if (points.length > 0 && forecasts.length > 0) {
    const lastIdx = points.length - 1;
    data[lastIdx].forecast_food = data[lastIdx].food_per_family;
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid {...CHART_GRID} />
        <XAxis dataKey="label" {...CHART_AXIS} />
        <YAxis yAxisId="left" {...CHART_AXIS} />
        <YAxis yAxisId="right" orientation="right" {...CHART_AXIS} />
        <Tooltip content={<ChartTooltip />} />
        <ReferenceLine
          yAxisId="right"
          y={5}
          stroke={CHART_COLORS.red}
          strokeDasharray="5 5"
          label={{ value: "Danger", fill: CHART_COLORS.red, fontSize: 10 }}
        />
        <Area
          yAxisId="left"
          type="monotone"
          dataKey="food_total"
          name="Food total"
          fill={CHART_COLORS.goldDim}
          fillOpacity={0.2}
          stroke={CHART_COLORS.goldDim}
          strokeWidth={1}
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="food_per_family"
          name="Food/family"
          stroke={CHART_COLORS.goldBright}
          strokeWidth={2}
          dot={{ r: 3, fill: CHART_COLORS.goldBright }}
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="forecast_food"
          name="Forecast"
          stroke={CHART_COLORS.goldBright}
          strokeWidth={2}
          strokeDasharray="6 4"
          strokeOpacity={0.5}
          dot={false}
          connectNulls={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
