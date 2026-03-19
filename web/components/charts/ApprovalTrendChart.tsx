"use client";

import {
  ResponsiveContainer, ComposedChart, Line, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ReferenceArea, ReferenceLine,
} from "recharts";
import { CHART_COLORS, CHART_GRID, CHART_AXIS } from "~/lib/chart-theme";
import { ChartTooltip } from "./ChartTooltip";
import type { TrendPoint, ForecastPoint } from "~/hooks/useTrends";

interface Props {
  points: TrendPoint[];
  forecasts: ForecastPoint[];
}

export function ApprovalTrendChart({ points, forecasts }: Props) {
  const data = [
    ...points.map((p) => ({
      label: p.label,
      approval: p.approval,
      homeless: p.homeless,
      forecast_approval: undefined as number | undefined,
    })),
    ...forecasts.map((f) => ({
      label: f.label,
      approval: undefined as number | undefined,
      homeless: undefined as number | undefined,
      forecast_approval: f.approval,
    })),
  ];

  if (points.length > 0 && forecasts.length > 0) {
    data[points.length - 1].forecast_approval = data[points.length - 1].approval;
  }

  return (
    <ResponsiveContainer width="100%" height={180}>
      <ComposedChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid {...CHART_GRID} />
        <XAxis dataKey="label" {...CHART_AXIS} />
        <YAxis yAxisId="left" domain={[0, 100]} {...CHART_AXIS} />
        <YAxis yAxisId="right" orientation="right" {...CHART_AXIS} />
        <Tooltip content={<ChartTooltip />} />
        <ReferenceArea yAxisId="left" y1={70} y2={100} fill={CHART_COLORS.green} fillOpacity={0.05} />
        <ReferenceArea yAxisId="left" y1={0} y2={50} fill={CHART_COLORS.red} fillOpacity={0.05} />
        <ReferenceLine yAxisId="left" y={50} stroke={CHART_COLORS.goldDim} strokeDasharray="3 3" />
        <Bar
          yAxisId="right"
          dataKey="homeless"
          name="Homeless"
          fill={CHART_COLORS.red}
          fillOpacity={0.6}
          barSize={12}
        />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="approval"
          name="Approval %"
          stroke={CHART_COLORS.green}
          strokeWidth={2}
          dot={{ r: 3, fill: CHART_COLORS.green }}
        />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="forecast_approval"
          name="Forecast"
          stroke={CHART_COLORS.green}
          strokeWidth={2}
          strokeDasharray="6 4"
          strokeOpacity={0.5}
          dot={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
