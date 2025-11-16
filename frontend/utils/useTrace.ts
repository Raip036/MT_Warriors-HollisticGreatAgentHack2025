import { useState, useEffect } from "react";

const BACKEND_URL = "http://localhost:8000";

export interface TraceStep {
  step_id: number;
  type: "decision" | "tool_call" | "memory_update" | "state_transition";
  timestamp: string;
  input: any;
  output: any;
  metadata: {
    summary?: string;
    agent?: string;
    duration_ms?: number;
    [key: string]: any;
  };
  tool_name?: string;
  duration_ms?: number;
  success: boolean;
  error?: string;
}

export interface Trace {
  session_id: string;
  started_at: string;
  ended_at?: string;
  steps: TraceStep[];
  metadata: {
    total_steps: number;
    total_tool_calls: number;
    total_decisions: number;
    total_memory_updates: number;
    duration_seconds?: number;
  };
}

export function useTrace(sessionId: string | null, enabled: boolean = true) {
  const [trace, setTrace] = useState<Trace | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId || !enabled) {
      setTrace(null);
      return;
    }

    const fetchTrace = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${BACKEND_URL}/trace/${sessionId}`);
        if (!response.ok) {
          if (response.status === 404) {
            // Trace might not be ready yet, that's okay
            setTrace(null);
            setLoading(false);
            return;
          }
          throw new Error(`Failed to fetch trace: ${response.statusText}`);
        }
        const data = await response.json();
        setTrace(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch trace");
        setTrace(null);
      } finally {
        setLoading(false);
      }
    };

    fetchTrace();
  }, [sessionId, enabled]);

  return { trace, loading, error };
}

