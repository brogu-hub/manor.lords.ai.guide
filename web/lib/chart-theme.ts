export const CHART_COLORS = {
  gold: "oklch(0.72 0.1 75)",
  goldBright: "oklch(0.82 0.1 80)",
  goldDim: "oklch(0.45 0.06 75)",
  green: "oklch(0.65 0.1 145)",
  red: "oklch(0.65 0.12 25)",
  parchment: "oklch(0.73 0.04 70)",
  panelBg: "oklch(0.18 0.01 55)",
  panelHeader: "oklch(0.22 0.015 55)",
  border: "oklch(0.3 0.02 55)",
  muted: "oklch(0.52 0.03 65)",
  // Series colors
  food: "oklch(0.65 0.12 85)",
  fuel: "oklch(0.6 0.1 30)",
  approval: "oklch(0.65 0.1 145)",
  population: "oklch(0.65 0.08 250)",
  wealth: "oklch(0.72 0.1 75)",
  devPoints: "oklch(0.6 0.1 260)",
} as const;

export const CHART_GRID = {
  stroke: CHART_COLORS.border,
  strokeDasharray: "3 3",
};

export const CHART_AXIS = {
  tick: { fill: CHART_COLORS.muted, fontSize: 11 },
  axisLine: { stroke: CHART_COLORS.border },
  tickLine: { stroke: CHART_COLORS.border },
};
