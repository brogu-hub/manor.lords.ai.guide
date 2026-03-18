import { Card, CardHeader, CardTitle, CardContent } from "~/components/ui/card";
import type { Advice } from "~/hooks/useSSE";

interface Props {
  advice: Advice | null;
}

export function WarningsPanel({ advice }: Props) {
  const warnings = advice?.warnings ?? [];

  return (
    <Card className="col-span-full bg-card border-border">
      <CardHeader className="bg-[var(--color-panel-header)] border-b border-[var(--color-gold-dim)] py-2.5 px-5">
        <CardTitle className="font-heading text-sm font-semibold text-primary uppercase tracking-wider">
          Warnings
        </CardTitle>
      </CardHeader>
      <CardContent className="p-4">
        {warnings.length > 0 ? (
          <div className="space-y-2">
            {warnings.map((w, i) => (
              <div
                key={i}
                className="px-4 py-2.5 bg-destructive/10 border-l-2 border-destructive text-destructive-foreground text-[0.9375rem] leading-7 rounded-sm"
              >
                {w}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-muted-foreground italic text-[0.9375rem]">
            No warnings — settlement is stable, my Lord.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
