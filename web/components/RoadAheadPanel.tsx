"use client";

import { Card, CardHeader, CardTitle, CardContent } from "~/components/ui/card";
import type { Advice } from "~/hooks/useSSE";

interface Props {
  advice: Advice | null;
}

export function RoadAheadPanel({ advice }: Props) {
  return (
    <Card className="bg-card border-border">
      <CardHeader className="bg-[var(--color-panel-header)] border-b border-[var(--color-gold-dim)] py-2.5 px-5">
        <CardTitle className="font-heading text-sm font-semibold text-primary uppercase tracking-wider">
          The Road Ahead
        </CardTitle>
      </CardHeader>
      <CardContent className="p-4">
        {advice?.road_ahead ? (
          <p className="text-[0.9375rem] leading-7 text-foreground whitespace-pre-line">
            {advice.road_ahead}
          </p>
        ) : (
          <p className="text-muted-foreground italic text-sm">
            Strategic plans will appear after analysis
          </p>
        )}
      </CardContent>
    </Card>
  );
}
