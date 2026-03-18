import { Card, CardHeader, CardTitle, CardContent } from "~/components/ui/card";
import type { Advice } from "~/hooks/useSSE";

interface Props {
  advice: Advice | null;
}

export function PrioritiesPanel({ advice }: Props) {
  const priorities = [
    advice?.priority_1,
    advice?.priority_2,
    advice?.priority_3,
  ].filter(Boolean);

  return (
    <Card className="bg-card border-border">
      <CardHeader className="bg-[var(--color-panel-header)] border-b border-[var(--color-gold-dim)] py-2.5 px-5">
        <CardTitle className="font-heading text-sm font-semibold text-primary uppercase tracking-wider">
          Royal Priorities
        </CardTitle>
      </CardHeader>
      <CardContent className="p-4">
        {priorities.length > 0 ? (
          <div className="space-y-2">
            {priorities.map((p, i) => (
              <div
                key={i}
                className="px-4 py-2.5 bg-[var(--color-ok-green)]/8 border-l-2 border-[var(--color-ok-green)] text-[0.9375rem] leading-7 rounded-sm"
              >
                <span className="font-heading text-[var(--color-ok-green-text)] text-xs">
                  #{i + 1}
                </span>{" "}
                {p}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-muted-foreground italic text-[0.9375rem]">
            Press &quot;Analyse Save&quot; to receive counsel
          </p>
        )}
      </CardContent>
    </Card>
  );
}
