import { Card, CardHeader, CardTitle, CardContent } from "~/components/ui/card";
import type { Advice } from "~/hooks/useSSE";

interface Props {
  advice: Advice | null;
}

export function SituationPanel({ advice }: Props) {
  return (
    <Card className="bg-card border-border">
      <CardHeader className="bg-[var(--color-panel-header)] border-b border-[var(--color-gold-dim)] py-2.5 px-5">
        <CardTitle className="font-heading text-sm font-semibold text-primary uppercase tracking-wider">
          State of the Realm
        </CardTitle>
      </CardHeader>
      <CardContent className="p-4">
        {advice?.situation ? (
          <p className="text-[0.9375rem] leading-7">{advice.situation}</p>
        ) : (
          <p className="text-muted-foreground italic text-[0.9375rem]">
            Awaiting the lord&apos;s ledger...
          </p>
        )}
      </CardContent>
    </Card>
  );
}
