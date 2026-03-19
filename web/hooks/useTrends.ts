"use client";

import { useState, useEffect } from "react";

export interface TrendPoint {
  id: number;
  timestamp: string;
  save_name: string;
  label: string;
  year: number;
  season: string;
  day: number;
  approval: number;
  families: number;
  workers: number;
  homeless: number;
  food_total: number;
  food_per_family: number;
  firewood: number;
  firewood_per_family: number;
  charcoal: number;
  timber: number;
  planks: number;
  stone: number;
  clay: number;
  leather: number;
  linen: number;
  shoes: number;
  cloaks: number;
  iron: number;
  ale: number;
  regional_wealth: number;
  development_points: number;
  retinue_count: number;
  bandit_camps_nearby: number;
  alert_count: number;
  worker_ratio: number;
  trajectory_label?: string;
  trajectory_score?: number;
}

export interface ForecastPoint {
  label: string;
  food_per_family?: number;
  firewood_per_family?: number;
  approval?: number;
  regional_wealth?: number;
  worker_ratio?: number;
  [key: string]: string | number | undefined;
}

export interface GamePathFactor {
  metric: string;
  direction: "rising" | "stable" | "falling";
  status: "good" | "warning" | "critical";
  value: number;
}

export interface GamePath {
  verdict: "improving" | "stable" | "declining" | "critical";
  score: number;
  factors: GamePathFactor[];
}

export interface SimilarState {
  id: number;
  label: string;
  score: number;
  reasoning: string;
  strengths: string[];
  risks: string[];
  similarity: number;
  year: number;
  season: string;
  families: number;
  save_name?: string;
}

export interface TrendsData {
  points: TrendPoint[];
  forecasts: ForecastPoint[];
  slopes: Record<string, number>;
  game_path: GamePath | null;
  similar_states: SimilarState[];
  count: number;
}

export function useTrends(refreshKey?: unknown) {
  const [data, setData] = useState<TrendsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch("/api/trends")
      .then((r) => r.json())
      .then((d) => setData(d))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [refreshKey]);

  return {
    points: data?.points ?? [],
    forecasts: data?.forecasts ?? [],
    slopes: data?.slopes ?? {},
    gamePath: data?.game_path ?? null,
    similarStates: data?.similar_states ?? [],
    latest: data?.points?.length ? data.points[data.points.length - 1] : null,
    count: data?.count ?? 0,
    loading,
  };
}
