import { Card, CardHeader, CardTitle, CardContent } from "~/components/ui/card";

interface HistoryEntry {
  timestamp: string;
  summary: string;
  priority_1?: string;
}

interface Props {
  entries: HistoryEntry[];
}

export function HistoryPanel({ entries }: Props) {
  return (
    <Card className="col-span-full bg-card border-border">
      <CardHeader className="bg-[var(--color-panel-header)] border-b border-[var(--color-gold-dim)] py-2 px-4">
        <CardTitle className="font-heading text-xs font-semibold text-primary uppercase tracking-wider">
          Chronicle
        </CardTitle>
      </CardHeader>
      <CardContent className="p-3">
        {entries.length > 0 ? (
          <div className="space-y-1.5">
            {entries.map((e, i) => (
              <div
                key={i}
                className="px-3 py-2 bg-[var(--color-ok-green)]/8 border-l-2 border-[var(--color-ok-green)] text-sm rounded-sm"
              >
                <span className="font-heading text-[var(--color-ok-green-text)] text-xs">
                  {e.timestamp}
                </span>{" "}
                {e.summary}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-muted-foreground italic text-sm">
            No records in the chronicle yet
          </p>
        )}
      </CardContent>
    </Card>
  );
}
