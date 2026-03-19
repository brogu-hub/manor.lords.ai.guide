"use client";

import { useState, useEffect, useCallback, useRef } from "react";

export interface Advice {
  warnings?: string[];
  priority_1?: string;
  priority_2?: string;
  priority_3?: string;
  situation?: string;
  next_season?: string;
}

export interface GameState {
  meta?: { year?: number; season?: string; day?: number };
  settlement?: {
    name?: string;
    approval?: number;
    population?: { families?: number; workers?: number; homeless?: number };
    regional_wealth?: number;
    lord_personal_wealth?: number;
  };
  resources?: {
    food?: {
      total?: number;
      bread?: number;
      berries?: number;
      meat?: number;
      vegetables?: number;
      eggs?: number;
      fish?: number;
    };
    fuel?: { firewood?: number; charcoal?: number };
    construction?: {
      timber?: number;
      planks?: number;
      stone?: number;
      clay?: number;
    };
    clothing?: {
      leather?: number;
      linen?: number;
      shoes?: number;
      cloaks?: number;
    };
    production?: {
      iron?: number;
      ale?: number;
      malt?: number;
      flour?: number;
      yarn?: number;
    };
  };
  buildings?: {
    type?: string;
    workers_assigned?: number;
    max_workers?: number;
    level?: number;
  }[];
  military?: {
    retinue_count?: number;
    retinue_equipment?: string;
    levies_mobilised?: boolean;
    bandit_camps_nearby?: number;
    active_raid?: boolean;
  };
  realm_map?: {
    resource_nodes?: {
      type?: string;
      rich?: boolean;
      direction?: string;
      distance?: string;
    }[];
    region_count?: number;
    settled_regions?: number;
    summary?: string;
  };
  development_points?: number;
  alerts?: string[];
  [key: string]: unknown;
}

export interface EvalResult {
  passed: boolean | null;
  scores: Record<string, number>;
  reasons: Record<string, string>;
  attempt: number;
}

type ConnectionStatus = "connecting" | "connected" | "disconnected";

export function useSSE() {
  const [advice, setAdvice] = useState<Advice | null>(null);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>("connecting");

  // Streaming state
  const [streamingText, setStreamingText] = useState("");
  const [thinkingText, setThinkingText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const streamAttemptRef = useRef(0);

  // Eval state
  const [evalResult, setEvalResult] = useState<EvalResult | null>(null);

  // Fetch latest state + advice on mount (survives refresh)
  useEffect(() => {
    fetch("/api/state")
      .then((r) => r.json())
      .then((data) => {
        if (data && data.meta) setGameState(data);
      })
      .catch(() => {});
    fetch("/api/advice")
      .then((r) => r.json())
      .then((data) => {
        if (data && data.priority_1) setAdvice(data);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    const evtSource = new EventSource("/api/stream");

    evtSource.onopen = () => {
      setStatus("connected");
      setError(null);
    };

    evtSource.addEventListener("advice", (e) => {
      const data = JSON.parse(e.data);
      setAdvice(data);
      setIsProcessing(false);
      setIsStreaming(false);
      setStreamingText("");
      setThinkingText("");
      setError(null);
    });

    evtSource.addEventListener("state", (e) => {
      const data = JSON.parse(e.data);
      setGameState(data);
    });

    evtSource.addEventListener("processing", () => {
      setIsProcessing(true);
      setError(null);
      setStreamingText("");
      setThinkingText("");
      setEvalResult(null);
    });

    evtSource.addEventListener("streaming_start", () => {
      setIsStreaming(true);
      setStreamingText("");
      setThinkingText("");
    });

    evtSource.addEventListener("streaming_end", () => {
      setIsStreaming(false);
    });

    evtSource.addEventListener("advice_chunk", (e) => {
      const data = JSON.parse(e.data);
      const attempt = data.attempt ?? 1;
      // Clear on new attempt
      if (attempt !== streamAttemptRef.current) {
        streamAttemptRef.current = attempt;
        setStreamingText("");
        setThinkingText("");
      }
      setStreamingText((prev) => prev + data.text);
    });

    evtSource.addEventListener("thinking_chunk", (e) => {
      const data = JSON.parse(e.data);
      const attempt = data.attempt ?? 1;
      if (attempt !== streamAttemptRef.current) {
        streamAttemptRef.current = attempt;
        setStreamingText("");
        setThinkingText("");
      }
      setThinkingText((prev) => prev + data.text);
    });

    evtSource.addEventListener("eval_result", (e) => {
      const data = JSON.parse(e.data);
      setEvalResult(data);
    });

    evtSource.addEventListener("error", (e: Event) => {
      const msgEvent = e as MessageEvent;
      try {
        const data = JSON.parse(msgEvent.data);
        setError(data.message || "Pipeline failed");
      } catch {
        setError("Pipeline error");
      }
      setIsProcessing(false);
      setIsStreaming(false);
    });

    evtSource.onerror = () => {
      setStatus("disconnected");
    };

    return () => evtSource.close();
  }, []);

  const processSave = useCallback(async (saveName?: string) => {
    setIsProcessing(true);
    setError(null);
    setEvalResult(null);
    try {
      const url = saveName
        ? `/api/process?save_name=${encodeURIComponent(saveName)}`
        : "/api/process";
      const resp = await fetch(url, { method: "POST" });
      const data = await resp.json();
      if (data.status === "error" || data.status === "busy") {
        setError(data.message);
        setIsProcessing(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
      setIsProcessing(false);
    }
  }, []);

  const askQuestion = useCallback(async (question: string) => {
    const resp = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await resp.json();
    return data.answer as string;
  }, []);

  const loadHistoryEntry = useCallback(async (entryId: number) => {
    try {
      const resp = await fetch(`/api/history/${entryId}`);
      const data = await resp.json();
      if (data.state) setGameState(data.state);
      if (data.advice) setAdvice(data.advice);
      setStreamingText("");
      setThinkingText("");
      setEvalResult(null);
      return data;
    } catch {
      return null;
    }
  }, []);

  return {
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
  };
}
