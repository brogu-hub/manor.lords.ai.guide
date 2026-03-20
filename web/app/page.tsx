"use client";

import { useState, useEffect } from "react";
import { Button } from "~/components/ui/button";
import { Badge } from "~/components/ui/badge";
import { useSSE } from "~/hooks/useSSE";
import { StateBar } from "~/components/StateBar";
import { StreamingPanel } from "~/components/StreamingPanel";
import { EvalBadge } from "~/components/EvalBadge";
import { WarningsPanel } from "~/components/WarningsPanel";
import { PrioritiesPanel } from "~/components/PrioritiesPanel";
import { SituationPanel } from "~/components/SituationPanel";
import { NextSeasonPanel } from "~/components/NextSeasonPanel";
import { ChatPanel } from "~/components/ChatPanel";
import { HistoryPanel } from "~/components/HistoryPanel";
import { SaveSelector } from "~/components/SaveSelector";
import { UploadZone } from "~/components/UploadZone";
import { PopOutButton } from "~/components/PopOutButton";
import { TrendsPanel } from "~/components/TrendsPanel";
import { RealmMapPanel } from "~/components/RealmMapPanel";
import { PatchNotesPanel } from "~/components/PatchNotesPanel";
import { RoadAheadPanel } from "~/components/RoadAheadPanel";

export default function Dashboard() {
  const {
    advice,
    gameState,
    isProcessing,
    error,
    status,
    streamingText,
    thinkingText,
    isStreaming,
    evalResult,
    processSave,
    askQuestion,
    loadHistoryEntry,
  } = useSSE();
  const [selectedSave, setSelectedSave] = useState<string | undefined>();
  const [history, setHistory] = useState<
    { id?: number; timestamp: string; save_name?: string; summary: string; priority_1?: string }[]
  >([]);
  const [activeHistoryId, setActiveHistoryId] = useState<number | null>(null);
  const [hasSaves, setHasSaves] = useState(true);

  // Fetch history on mount and after advice updates
  useEffect(() => {
    fetch("/api/history")
      .then((r) => r.json())
      .then((data) => setHistory(data.entries ?? []))
      .catch(() => {});
    // Clear history selection when new live advice arrives
    setActiveHistoryId(null);
  }, [advice]);

  // Check if local saves exist (for showing upload zone if needed)
  useEffect(() => {
    fetch("/api/saves")
      .then((r) => r.json())
      .then((data) => setHasSaves((data.saves ?? []).length > 0))
      .catch(() => setHasSaves(false));
  }, []);

  const statusText = isStreaming
    ? "Streaming response..."
    : isProcessing
      ? "Analysing save..."
      : error
        ? `Error: ${error}`
        : status === "connected"
          ? advice
            ? `Updated ${new Date().toLocaleTimeString()}`
            : "Connected"
          : status === "connecting"
            ? "Connecting..."
            : "Reconnecting...";

  const statusColor = isStreaming
    ? "text-primary animate-pulse-gold"
    : isProcessing
      ? "text-primary animate-pulse-gold"
      : error
        ? "text-destructive-foreground"
        : status === "connected"
          ? "text-[var(--color-ok-green-text)]"
          : "text-muted-foreground";

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 bg-card border-b border-[var(--color-gold-dim)]">
        <div className="flex items-center gap-3">
          <svg
            className="text-primary opacity-80"
            viewBox="0 0 24 24"
            width="26"
            height="26"
            fill="currentColor"
          >
            <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 2.18l7 3.12v4.7c0 4.83-3.13 9.37-7 10.65-3.87-1.28-7-5.82-7-10.65V6.3l7-3.12z" />
          </svg>
          <h1 className="font-heading text-lg font-semibold text-primary uppercase tracking-wider">
            Manor Lords Advisor
          </h1>
        </div>

        <div className="flex items-center gap-3">
          {evalResult && <EvalBadge evalResult={evalResult} />}
          <PopOutButton />
          <SaveSelector selected={selectedSave} onSelect={setSelectedSave} />
          <Button
            onClick={() => processSave(selectedSave)}
            disabled={isProcessing}
            className="font-heading text-xs font-semibold uppercase tracking-wide bg-[var(--color-gold-dim)] text-[var(--color-gold-bright)] border border-ring hover:bg-ring hover:text-primary-foreground h-9 px-4"
          >
            <svg
              viewBox="0 0 24 24"
              width="14"
              height="14"
              fill="currentColor"
              className="mr-1.5"
            >
              <path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46C19.54 15.03 20 13.57 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74C4.46 8.97 4 10.43 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z" />
            </svg>
            {isProcessing ? "Analysing..." : "Analyse Save"}
          </Button>
          <Badge
            variant="outline"
            className={`text-xs italic font-sans border-none ${statusColor}`}
          >
            {statusText}
          </Badge>
        </div>
      </header>

      {/* Main Grid */}
      <main className="flex-1 grid grid-cols-2 gap-2.5 p-3 overflow-y-auto">
        <StateBar state={gameState} />

        {/* Realm map — cartographer's survey */}
        <RealmMapPanel state={gameState} />

        {/* Trends panel — charts, forecasts, game path */}
        <TrendsPanel advice={advice} season={gameState?.meta?.season} />

        {/* Streaming panel — shows during AI generation */}
        <StreamingPanel
          streamingText={streamingText}
          thinkingText={thinkingText}
          isStreaming={isStreaming}
          isProcessing={isProcessing}
        />

        <WarningsPanel advice={advice} />
        <PrioritiesPanel advice={advice} />
        <SituationPanel advice={advice} />
        <NextSeasonPanel advice={advice} />
        <RoadAheadPanel advice={advice} />

        {!hasSaves && <UploadZone onUploaded={() => setHasSaves(true)} />}

        <PatchNotesPanel gameVersion={gameState?.meta?.game_version} />
        <ChatPanel askQuestion={askQuestion} hasState={!!gameState} />
        <HistoryPanel
          entries={history}
          activeId={activeHistoryId}
          onSelect={async (id) => {
            setActiveHistoryId(id);
            await loadHistoryEntry(id);
          }}
        />
      </main>
    </div>
  );
}
