"use client";

import {
  ResponsiveContainer, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from "recharts";
import { CHART_COLORS, CHART_GRID, CHART_AXIS } from "~/lib/chart-theme";
import { ChartTooltip } from "./ChartTooltip";
import type { TrendPoint, ForecastPoint } from "~/hooks/useTrends";

interface Props {
  points: TrendPoint[];
  forecasts: ForecastPoint[];
}

export function EconomyOverviewChart({ points, forecasts }: Props) {
  const data = [
    ...points.map((p) => ({
      label: p.label,
      wealth: p.regional_wealth,
      dev_points: p.development_points,
      families: p.families,
      forecast_wealth: undefined as number | undefined,
    })),
    ...forecasts.map((f) => ({
      label: f.label,
      wealth: undefined as number | undefined,
      dev_points: undefined as number | undefined,
      families: undefined as number | undefined,
      forecast_wealth: f.regional_wealth,
    })),
  ];

  if (points.length > 0 && forecasts.length > 0) {
    data[points.length - 1].forecast_wealth = data[points.length - 1].wealth;
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid {...CHART_GRID} />
        <XAxis dataKey="label" {...CHART_AXIS} />
        <YAxis yAxisId="left" {...CHART_AXIS} />
        <YAxis yAxisId="right" orientation="right" {...CHART_AXIS} />
        <Tooltip content={<ChartTooltip />} />
        <Legend
          wrapperStyle={{ fontSize: 11, color: CHART_COLORS.muted }}
        />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="wealth"
          name="Wealth"
          stroke={CHART_COLORS.wealth}
          strokeWidth={2}
          dot={{ r: 3, fill: CHART_COLORS.wealth }}
        />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="dev_points"
          name="Dev Points"
          stroke={CHART_COLORS.devPoints}
          strokeWidth={2}
          dot={{ r: 3, fill: CHART_COLORS.devPoints }}
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="families"
          name="Families"
          stroke={CHART_COLORS.population}
          strokeWidth={2}
          dot={{ r: 3, fill: CHART_COLORS.population }}
        />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="forecast_wealth"
          name="Wealth forecast"
          stroke={CHART_COLORS.wealth}
          strokeWidth={2}
          strokeDasharray="6 4"
          strokeOpacity={0.5}
          dot={false}
          legendType="none"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
