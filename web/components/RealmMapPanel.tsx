"use client";

import { Card, CardHeader, CardTitle, CardContent } from "~/components/ui/card";
import type { GameState } from "~/hooks/useSSE";

interface Props {
  state: GameState | null;
}

// Compass direction → angle in degrees (0 = right/east, counter-clockwise)
const DIRECTION_ANGLE: Record<string, number> = {
  east: 0,
  "north-east": 45,
  north: 90,
  "north-west": 135,
  west: 180,
  "south-west": 225,
  south: 270,
  "south-east": 315,
};

// Distance → radius ratio (0-1)
const DISTANCE_RADIUS: Record<string, number> = {
  nearby: 0.25,
  "a short ride": 0.45,
  "a fair distance": 0.65,
  "far afield": 0.85,
};

// Resource type → icon/color
const NODE_STYLE: Record<string, { color: string; symbol: string }> = {
  "iron deposit": { color: "oklch(0.55 0.08 250)", symbol: "\u2692" },       // hammer & pick
  "stone quarry": { color: "oklch(0.6 0.03 80)", symbol: "\u25C6" },         // diamond
  "clay pit": { color: "oklch(0.55 0.1 50)", symbol: "\u25CF" },             // circle
  "berry thicket": { color: "oklch(0.55 0.15 340)", symbol: "\u273F" },      // flower
  "hunting grounds": { color: "oklch(0.55 0.1 120)", symbol: "\u2726" },     // star
  "fishing waters": { color: "oklch(0.6 0.1 230)", symbol: "\u2248" },       // waves
  "eel pond": { color: "oklch(0.55 0.08 210)", symbol: "\u223C" },           // tilde
  "salt spring": { color: "oklch(0.7 0.05 80)", symbol: "\u2662" },          // diamond suit
  "mushroom grove": { color: "oklch(0.5 0.08 100)", symbol: "\u2618" },      // shamrock
  "bandit camp": { color: "oklch(0.6 0.15 25)", symbol: "\u2620" },          // skull
};

export function RealmMapPanel({ state }: Props) {
  const realmMap = state?.realm_map;
  const nodes = realmMap?.resource_nodes ?? [];
  const settlement = state?.settlement;

  const size = 320;
  const cx = size / 2;
  const cy = size / 2;
  const maxR = size / 2 - 30;

  // Group nodes by type for the legend
  const typeSet = new Map<string, { color: string; symbol: string; count: number; rich: number }>();
  for (const n of nodes) {
    const t = n.type ?? "unknown";
    const style = NODE_STYLE[t] ?? { color: "oklch(0.5 0.05 60)", symbol: "?" };
    const existing = typeSet.get(t);
    if (existing) {
      existing.count++;
      if (n.rich) existing.rich++;
    } else {
      typeSet.set(t, { ...style, count: 1, rich: n.rich ? 1 : 0 });
    }
  }

  return (
    <Card className="col-span-full bg-card border-border">
      <CardHeader className="bg-[var(--color-panel-header)] border-b border-[var(--color-gold-dim)] py-2.5 px-5">
        <CardTitle className="font-heading text-sm font-semibold text-primary uppercase tracking-wider">
          Cartographer&apos;s Survey
          {realmMap && (
            <span className="text-muted-foreground font-normal text-xs ml-2">
              {realmMap.region_count} territories, {realmMap.settled_regions} settled
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="p-4">
        {!realmMap || nodes.length === 0 ? (
          <p className="text-sm text-muted-foreground italic text-center py-6">
            The land awaits surveying, my lord
          </p>
        ) : (
          <div className="grid grid-cols-[1fr_auto] gap-6">
            {/* SVG compass map */}
            <div className="flex justify-center">
              <svg
                viewBox={`0 0 ${size} ${size}`}
                width={size}
                height={size}
                className="max-w-full"
              >
                {/* Background */}
                <circle cx={cx} cy={cy} r={maxR} fill="oklch(0.16 0.01 55)" stroke="oklch(0.3 0.02 55)" strokeWidth={1} />

                {/* Distance rings */}
                {[0.25, 0.45, 0.65, 0.85].map((r) => (
                  <circle
                    key={r}
                    cx={cx}
                    cy={cy}
                    r={maxR * r}
                    fill="none"
                    stroke="oklch(0.25 0.02 55)"
                    strokeWidth={0.5}
                    strokeDasharray="3 3"
                  />
                ))}

                {/* Compass lines */}
                {[0, 45, 90, 135].map((angle) => {
                  const rad = (angle * Math.PI) / 180;
                  return (
                    <line
                      key={angle}
                      x1={cx + maxR * Math.cos(rad)}
                      y1={cy - maxR * Math.sin(rad)}
                      x2={cx - maxR * Math.cos(rad)}
                      y2={cy + maxR * Math.sin(rad)}
                      stroke="oklch(0.22 0.015 55)"
                      strokeWidth={0.5}
                    />
                  );
                })}

                {/* Compass labels */}
                <text x={cx} y={12} textAnchor="middle" fill="oklch(0.52 0.03 65)" fontSize={10} fontFamily="var(--font-heading)">N</text>
                <text x={size - 10} y={cy + 4} textAnchor="middle" fill="oklch(0.52 0.03 65)" fontSize={10} fontFamily="var(--font-heading)">E</text>
                <text x={cx} y={size - 5} textAnchor="middle" fill="oklch(0.52 0.03 65)" fontSize={10} fontFamily="var(--font-heading)">S</text>
                <text x={12} y={cy + 4} textAnchor="middle" fill="oklch(0.52 0.03 65)" fontSize={10} fontFamily="var(--font-heading)">W</text>

                {/* Distance labels */}
                <text x={cx + 6} y={cy - maxR * 0.25 + 4} fill="oklch(0.4 0.02 55)" fontSize={7}>nearby</text>
                <text x={cx + 6} y={cy - maxR * 0.65 + 4} fill="oklch(0.4 0.02 55)" fontSize={7}>a fair distance</text>

                {/* Settlement center */}
                <g>
                  <circle cx={cx} cy={cy} r={8} fill="oklch(0.45 0.06 75)" fillOpacity={0.3} stroke="oklch(0.72 0.1 75)" strokeWidth={1.5} />
                  <text x={cx} y={cy + 3} textAnchor="middle" fill="oklch(0.82 0.1 80)" fontSize={8}>
                    &#x1F3F0;
                  </text>
                </g>

                {/* Resource nodes */}
                {nodes.map((node, i) => {
                  const angle = DIRECTION_ANGLE[node.direction ?? ""] ?? 0;
                  const r = (DISTANCE_RADIUS[node.distance ?? ""] ?? 0.5) * maxR;
                  const rad = (angle * Math.PI) / 180;
                  const x = cx + r * Math.cos(rad);
                  const y = cy - r * Math.sin(rad); // SVG y is inverted
                  const style = NODE_STYLE[node.type ?? ""] ?? { color: "oklch(0.5 0.05 60)", symbol: "?" };
                  const nodeR = node.rich ? 6 : 4;

                  // Jitter overlapping nodes slightly
                  const jx = x + ((i * 7) % 11 - 5);
                  const jy = y + ((i * 13) % 9 - 4);

                  return (
                    <g key={i}>
                      <circle
                        cx={jx}
                        cy={jy}
                        r={nodeR}
                        fill={style.color}
                        fillOpacity={node.rich ? 0.9 : 0.5}
                        stroke={node.rich ? "oklch(0.82 0.1 80)" : "none"}
                        strokeWidth={node.rich ? 1 : 0}
                      />
                      <text
                        x={jx}
                        y={jy + 3.5}
                        textAnchor="middle"
                        fill="oklch(0.9 0.02 70)"
                        fontSize={node.rich ? 8 : 6}
                      >
                        {style.symbol}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>

            {/* Legend + summary */}
            <div className="space-y-3 min-w-[180px]">
              <div>
                <h4 className="font-heading text-xs text-muted-foreground uppercase tracking-wider mb-2">
                  Resources Surveyed
                </h4>
                <div className="space-y-1">
                  {Array.from(typeSet.entries()).map(([type, info]) => (
                    <div key={type} className="flex items-center gap-2 text-xs">
                      <span style={{ color: info.color }} className="text-sm w-4 text-center">
                        {info.symbol}
                      </span>
                      <span className="text-foreground capitalize flex-1">{type}</span>
                      <span className="text-muted-foreground">
                        {info.count}
                        {info.rich > 0 && (
                          <span className="text-[var(--color-gold-bright)] ml-1">
                            ({info.rich} rich)
                          </span>
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Gerald's survey note */}
              {realmMap.summary && (
                <div className="border-t border-border pt-2">
                  <h4 className="font-heading text-xs text-muted-foreground uppercase tracking-wider mb-1">
                    Gerald&apos;s Survey Notes
                  </h4>
                  <p className="text-xs text-muted-foreground leading-relaxed italic">
                    {realmMap.summary}
                  </p>
                </div>
              )}

              {/* Settlement info */}
              {settlement && (
                <div className="border-t border-border pt-2">
                  <div className="flex items-center gap-1.5 text-xs">
                    <span className="text-primary">&#x1F3F0;</span>
                    <span className="text-foreground font-semibold">{settlement.name}</span>
                    <span className="text-muted-foreground">
                      — {settlement.population?.families ?? 0} families
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
