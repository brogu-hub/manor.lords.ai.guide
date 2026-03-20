"use client";

import { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "~/components/ui/card";

interface PatchNote {
  title: string;
  date: string;
  gid: string;
  content: string;
  url: string;
}

interface Props {
  gameVersion?: string;
}

export function PatchNotesPanel({ gameVersion }: Props) {
  const [notes, setNotes] = useState<PatchNote[]>([]);
  const [storeUrl, setStoreUrl] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/patch-notes")
      .then((r) => r.json())
      .then((data) => {
        setNotes(data.notes ?? []);
        setStoreUrl(data.store_url ?? "");
      })
      .catch(() => {});
  }, []);

  if (notes.length === 0) return null;

  const latest = notes[0];
  const isNew = latest && isRecentDate(latest.date);

  // Extract version from latest patch title (e.g. "0.8.065" from content)
  const latestPatchVersion = extractVersion(latest?.content ?? latest?.title ?? "");
  const saveVersion = gameVersion?.replace("Version ", "").trim();
  const versionMismatch = saveVersion && latestPatchVersion && saveVersion !== latestPatchVersion;

  return (
    <Card className="col-span-full bg-card border-border">
      <CardHeader className="bg-[var(--color-panel-header)] border-b border-[var(--color-gold-dim)] py-2.5 px-5">
        <div className="flex items-center justify-between">
          <CardTitle className="font-heading text-sm font-semibold text-primary uppercase tracking-wider">
            Royal Decrees
            <span className="text-muted-foreground font-normal text-xs ml-2">
              Patch Notes from the Realm
            </span>
          </CardTitle>
          <div className="flex items-center gap-2">
            {saveVersion && (
              <span className={`text-xs font-heading px-2 py-0.5 rounded-sm ${
                versionMismatch
                  ? "text-[var(--color-gold-bright)] bg-[var(--color-gold-dim)]/15"
                  : "text-muted-foreground"
              }`}>
                Save: {saveVersion}
                {versionMismatch && latestPatchVersion && ` \u2192 ${latestPatchVersion} available`}
              </span>
            )}
            {isNew && (
              <span className="text-xs font-heading uppercase tracking-wider text-[var(--color-ok-green-text)] bg-[var(--color-ok-green)]/10 px-2 py-0.5 rounded-sm">
                New Update
              </span>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-3">
        <div className="space-y-2">
          {notes.map((note) => (
            <div
              key={note.gid}
              className="border-l-2 border-[var(--color-gold-dim)] rounded-sm overflow-hidden"
            >
              <button
                type="button"
                onClick={() => setExpanded(expanded === note.gid ? null : note.gid)}
                className="w-full text-left px-3 py-2 hover:bg-secondary/30 transition-colors cursor-pointer"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-primary">&#x1F4DC;</span>
                    <span className="text-sm text-foreground font-semibold">
                      {note.title}
                    </span>
                  </div>
                  <span className="font-heading text-xs text-muted-foreground">
                    {note.date}
                  </span>
                </div>
              </button>

              {expanded === note.gid && (
                <div className="px-3 pb-3 border-t border-border/50">
                  <p className="text-xs text-muted-foreground leading-relaxed mt-2 whitespace-pre-line">
                    {note.content}
                    {note.content.length >= 498 && "..."}
                  </p>
                  <a
                    href={note.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-primary hover:text-[var(--color-gold-bright)] mt-2 transition-colors"
                  >
                    Read full decree on Steam &#x2192;
                  </a>
                </div>
              )}
            </div>
          ))}
        </div>

        {storeUrl && (
          <div className="mt-3 pt-2 border-t border-border">
            <a
              href={storeUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-muted-foreground hover:text-primary transition-colors"
            >
              View all decrees on Steam &#x2192;
            </a>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function isRecentDate(dateStr: string): boolean {
  try {
    const date = new Date(dateStr);
    const now = new Date();
    const diffDays = (now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24);
    return diffDays <= 14;
  } catch {
    return false;
  }
}

function extractVersion(text: string): string {
  // Match patterns like "0.8.065", "0.8.061", "Version 0.8.059"
  const match = text.match(/\b(\d+\.\d+\.\d+)\b/);
  return match ? match[1] : "";
}
