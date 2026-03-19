"use client";

import { Card, CardHeader, CardTitle, CardContent } from "~/components/ui/card";

function formatLocalTime(ts: string): string {
  try {
    return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return ts;
  }
}

interface HistoryEntry {
  id?: number;
  timestamp: string;
  save_name?: string;
  summary: string;
  priority_1?: string;
}

interface Props {
  entries: HistoryEntry[];
  activeId?: number | null;
  onSelect?: (id: number) => void;
}

export function HistoryPanel({ entries, activeId, onSelect }: Props) {
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
              <button
                key={e.id ?? i}
                type="button"
                onClick={() => e.id && onSelect?.(e.id)}
                className={`w-full text-left px-3 py-2 border-l-2 text-sm rounded-sm transition-colors ${
                  activeId === e.id
                    ? "bg-[var(--color-gold-dim)]/20 border-[var(--color-gold-bright)] text-[var(--color-gold-bright)]"
                    : "bg-[var(--color-ok-green)]/8 border-[var(--color-ok-green)] hover:bg-[var(--color-ok-green)]/15 cursor-pointer"
                }`}
              >
                <span className="font-heading text-[var(--color-ok-green-text)] text-xs">
                  {formatLocalTime(e.timestamp)}
                </span>
                {e.save_name && (
                  <span className="text-muted-foreground text-xs ml-1.5">
                    [{e.save_name.replace(".sav", "")}]
                  </span>
                )}
                {" "}
                {e.summary}
              </button>
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
