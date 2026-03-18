import { useSSE } from "~/hooks/useSSE";
import { StateBar } from "~/components/StateBar";
import { StreamingPanel } from "~/components/StreamingPanel";
import { ChatPanel } from "~/components/ChatPanel";

export function meta() {
  return [{ title: "Advisor — Pop Out" }];
}

export default function Popout() {
  const {
    advice,
    gameState,
    isProcessing,
    isStreaming,
    streamingText,
    thinkingText,
    askQuestion,
  } = useSSE();

  const priorities = [
    advice?.priority_1,
    advice?.priority_2,
    advice?.priority_3,
  ].filter(Boolean);

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      {/* Compact Header */}
      <header className="flex items-center justify-between px-3 py-2 bg-card border-b border-[var(--color-gold-dim)]">
        <h1 className="font-heading text-xs font-semibold text-primary uppercase tracking-wider">
          Advisor
        </h1>
        {(isProcessing || isStreaming) && (
          <span className="text-xs text-primary italic animate-pulse-gold">
            {isStreaming ? "Streaming..." : "Analysing..."}
          </span>
        )}
      </header>

      {/* State Bar */}
      <div className="p-1.5">
        <StateBar state={gameState} />
      </div>

      {/* Streaming panel */}
      <StreamingPanel
        streamingText={streamingText}
        thinkingText={thinkingText}
        isStreaming={isStreaming}
        isProcessing={isProcessing}
      />

      {/* Priorities */}
      <div className="px-3 pb-1.5">
        <h2 className="font-heading text-[0.65rem] text-primary uppercase tracking-wider mb-1.5 px-1">
          Priorities
        </h2>
        {priorities.length > 0 ? (
          <div className="space-y-1.5">
            {priorities.map((p, i) => (
              <div
                key={i}
                className="px-3 py-2 bg-[var(--color-ok-green)]/8 border-l-2 border-[var(--color-ok-green)] text-sm rounded-sm leading-relaxed"
              >
                <span className="font-heading text-[var(--color-ok-green-text)]">
                  #{i + 1}
                </span>{" "}
                {p}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-muted-foreground italic text-sm px-1">
            No advice yet
          </p>
        )}
      </div>

      {/* Warnings */}
      {advice?.warnings && advice.warnings.length > 0 && (
        <div className="px-3 pb-1.5">
          <h2 className="font-heading text-[0.65rem] text-destructive-foreground uppercase tracking-wider mb-1.5 px-1">
            Warnings
          </h2>
          <div className="space-y-1.5">
            {advice.warnings.map((w, i) => (
              <div
                key={i}
                className="px-3 py-2 bg-destructive/10 border-l-2 border-destructive text-destructive-foreground text-sm rounded-sm leading-relaxed"
              >
                {w}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chat */}
      <div className="flex-1 flex flex-col min-h-0 px-1.5 pb-1.5">
        <ChatPanel askQuestion={askQuestion} hasState={!!gameState} />
      </div>
    </div>
  );
}
