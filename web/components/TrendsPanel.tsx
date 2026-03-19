"use client";

import { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "~/components/ui/card";
import { useTrends } from "~/hooks/useTrends";
import { ResourceTrendChart } from "~/components/charts/ResourceTrendChart";
import { ApprovalTrendChart } from "~/components/charts/ApprovalTrendChart";
import { EconomyOverviewChart } from "~/components/charts/EconomyOverviewChart";
import { WinterReadinessGauge } from "~/components/charts/WinterReadinessGauge";
import { SurplusAdvisor } from "~/components/charts/SurplusAdvisor";
import { GamePathCard } from "~/components/charts/GamePathCard";
import type { Advice } from "~/hooks/useSSE";

interface Props {
  advice: Advice | null;
  season?: string;
}

export function TrendsPanel({ advice, season }: Props) {
  const [expanded, setExpanded] = useState(true);
  const { points, forecasts, gamePath, similarStates, latest, count } = useTrends(advice);

  // Collapsed summary line
  const summaryParts: string[] = [];
  if (gamePath) {
    summaryParts.push(`Score: ${gamePath.score} ${gamePath.verdict}`);
  }
  if (latest) {
    const fpf = latest.food_per_family;
    summaryParts.push(`Food: ${fpf.toFixed(1)}/family`);
    summaryParts.push(`Approval: ${latest.approval.toFixed(0)}%`);
  }

  return (
    <Card className="col-span-full bg-card border-border">
      <CardHeader
        className="bg-[var(--color-panel-header)] border-b border-[var(--color-gold-dim)] py-2 px-4 cursor-pointer select-none"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between">
          <CardTitle className="font-heading text-sm font-semibold text-primary uppercase tracking-wider">
            Realm Trends
            {count > 0 && (
              <span className="text-muted-foreground font-normal text-xs ml-2">
                ({count} snapshots)
              </span>
            )}
          </CardTitle>
          <div className="flex items-center gap-3">
            {!expanded && summaryParts.length > 0 && (
              <span className="text-xs text-muted-foreground">
                {summaryParts.join(" | ")}
              </span>
            )}
            <span className="text-muted-foreground text-xs">
              {expanded ? "\u25B2" : "\u25BC"}
            </span>
          </div>
        </div>
      </CardHeader>
      {expanded && (
        <CardContent className="p-3">
          {count === 0 ? (
            <p className="text-sm text-muted-foreground italic text-center py-6">
              Analyse a save to see realm trends
            </p>
          ) : (
            <div className="space-y-3">
              {/* Row 1: Resource trend (full width) */}
              <div>
                <h3 className="font-heading text-xs text-muted-foreground uppercase tracking-wider mb-1">
                  Food Sustainability
                </h3>
                {count >= 2 ? (
                  <ResourceTrendChart points={points} forecasts={forecasts} />
                ) : (
                  <p className="text-xs text-muted-foreground italic py-4 text-center">
                    Analyse 2+ saves to see trends
                  </p>
                )}
              </div>

              {/* Row 2: Approval + Winter Readiness */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <h3 className="font-heading text-xs text-muted-foreground uppercase tracking-wider mb-1">
                    Approval &amp; Housing
                  </h3>
                  {count >= 2 ? (
                    <ApprovalTrendChart points={points} forecasts={forecasts} />
                  ) : (
                    <p className="text-xs text-muted-foreground italic py-4 text-center">
                      Analyse 2+ saves to see trends
                    </p>
                  )}
                </div>
                <div>
                  <h3 className="font-heading text-xs text-muted-foreground uppercase tracking-wider mb-1">
                    Seasonal Readiness
                  </h3>
                  <WinterReadinessGauge latest={latest} season={season} />
                </div>
              </div>

              {/* Row 3: Surplus Advisor + Game Path */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <h3 className="font-heading text-xs text-muted-foreground uppercase tracking-wider mb-1">
                    Castle Readiness
                  </h3>
                  <SurplusAdvisor latest={latest} />
                </div>
                <div>
                  <h3 className="font-heading text-xs text-muted-foreground uppercase tracking-wider mb-1">
                    Game Path
                  </h3>
                  <GamePathCard
                    gamePath={gamePath}
                    similarStates={similarStates}
                    latest={latest}
                  />
                </div>
              </div>

              {/* Row 4: Economy (full width) */}
              {count >= 2 && (
                <div>
                  <h3 className="font-heading text-xs text-muted-foreground uppercase tracking-wider mb-1">
                    Economy Overview
                  </h3>
                  <EconomyOverviewChart points={points} forecasts={forecasts} />
                </div>
              )}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
