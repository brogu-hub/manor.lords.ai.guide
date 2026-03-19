"use client";

import { useEffect, useRef, useState } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "~/components/ui/card";

interface Props {
  streamingText: string;
  thinkingText: string;
  isStreaming: boolean;
  isProcessing: boolean;
}

export function StreamingPanel({
  streamingText,
  thinkingText,
  isStreaming,
  isProcessing,
}: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [showThinking, setShowThinking] = useState(false);

  // Auto-scroll to bottom as text streams in
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [streamingText, thinkingText]);

  if (!isProcessing && !isStreaming && !streamingText) return null;

  const hasThinking = thinkingText.length > 0;
  const hasResponse = streamingText.length > 0;

  return (
    <Card className="col-span-full bg-card border-border">
      <CardHeader className="bg-[var(--color-panel-header)] border-b border-[var(--color-gold-dim)] py-2.5 px-5">
        <div className="flex items-center justify-between">
          <CardTitle className="font-heading text-sm font-semibold text-primary uppercase tracking-wider flex items-center gap-2.5">
            {isStreaming && (
              <span className="inline-block w-2 h-2 rounded-full bg-primary animate-pulse-gold" />
            )}
            AI Response
            {isProcessing && !isStreaming && !hasResponse && (
              <span className="text-xs text-muted-foreground font-sans normal-case tracking-normal italic ml-1">
                Preparing...
              </span>
            )}
          </CardTitle>
          {hasThinking && (
            <button
              onClick={() => setShowThinking((v) => !v)}
              className="text-xs text-muted-foreground hover:text-foreground font-sans transition-colors"
            >
              {showThinking ? "Hide" : "Show"} thinking
              {thinkingText.length > 0 && (
                <span className="ml-1 text-[var(--color-gold-dim)]">
                  ({Math.round(thinkingText.length / 4)} tokens)
                </span>
              )}
            </button>
          )}
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {/* Thinking section (collapsible) */}
        {hasThinking && showThinking && (
          <div className="px-5 py-3 bg-secondary/30 border-b border-border">
            <p className="text-xs font-heading text-muted-foreground uppercase tracking-wider mb-1.5">
              Thinking
            </p>
            <pre className="text-sm text-muted-foreground italic whitespace-pre-wrap break-words leading-relaxed max-h-48 overflow-y-auto font-sans">
              {thinkingText}
            </pre>
          </div>
        )}

        {/* Streaming response */}
        <div ref={scrollRef} className="px-5 py-4 max-h-96 overflow-y-auto">
          {hasResponse ? (
            <pre className="text-[0.9375rem] whitespace-pre-wrap break-words leading-7 font-sans">
              {streamingText}
              {isStreaming && (
                <span className="inline-block w-1.5 h-5 bg-primary ml-0.5 animate-pulse-gold align-text-bottom" />
              )}
            </pre>
          ) : isProcessing ? (
            <div className="flex items-center gap-3 py-2">
              <div className="flex gap-1.5">
                <span
                  className="w-2 h-2 rounded-full bg-primary animate-pulse-gold"
                  style={{ animationDelay: "0s" }}
                />
                <span
                  className="w-2 h-2 rounded-full bg-primary animate-pulse-gold"
                  style={{ animationDelay: "0.3s" }}
                />
                <span
                  className="w-2 h-2 rounded-full bg-primary animate-pulse-gold"
                  style={{ animationDelay: "0.6s" }}
                />
              </div>
              <span className="text-sm text-muted-foreground italic">
                Processing save file...
              </span>
            </div>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}
