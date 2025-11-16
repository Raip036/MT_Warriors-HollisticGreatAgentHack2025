const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export interface Insights {
  summary: {
    total_traces: number;
    total_tool_calls: number;
    total_successful_calls: number;
    total_failed_calls: number;
    overall_success_rate: number;
    shortcut_rate: number;
    total_errors: number;
    generated_at: string;
  };
  tool_metrics: {
    most_used_tools: Record<string, number>;
    tool_success_rates: Record<
      string,
      {
        success_rate: number;
        total_calls: number;
        successful: number;
        failed: number;
        avg_duration_ms: number;
        min_duration_ms: number;
        max_duration_ms: number;
      }
    >;
    tool_reliability_ranking: Array<[string, any]>;
  };
  step_metrics: {
    step_type_distribution: Record<string, number>;
    step_type_avg_latencies: Record<
      string,
      {
        avg_ms: number;
        min_ms: number;
        max_ms: number;
        count: number;
      }
    >;
  };
  shortcuts: {
    total_suspected: number;
    shortcut_rate: number;
    traces_with_shortcuts: Array<{
      session_id: string;
      details: any;
    }>;
  };
  error_patterns: {
    most_common_errors: Record<string, number>;
    errors_by_tool: Record<string, number>;
    errors_by_step_type: Record<string, number>;
    total_error_count: number;
  };
  bottlenecks: {
    slow_steps: Array<{
      step_type: string;
      avg_latency_ms: number;
      count: number;
    }>;
    unreliable_tools: Array<{
      tool: string;
      success_rate: number;
      total_calls: number;
    }>;
    high_error_tools: Array<{
      tool: string;
      error_count: number;
    }>;
  };
  recommendations: string[];
  failure_analysis: {
    total_traces_with_failures: number;
    total_failures: number;
    failure_rate: number;
    failures_by_root_cause: Record<string, number>;
    failures_by_tool: Record<string, number>;
    failures_by_step_type: Record<string, number>;
    recurring_failures: Array<{
      pattern: string;
      count: number;
      root_cause: string;
    }>;
    failure_reports: Array<{
      session_id: string;
      total_failures: number;
      failures: Array<{
        step_id: number;
        step_type: string;
        tool_name?: string;
        error: string;
        timestamp: string;
        root_cause: string;
        derived_from_step_id?: number;
        severity: string;
        recommendation: string;
        confidence: number;
      }>;
    }>;
  };
}

export async function fetchInsights(): Promise<Insights> {
  const response = await fetch(`${BACKEND_URL}/insights`);
  if (!response.ok) {
    throw new Error(`Failed to fetch insights: ${response.statusText}`);
  }
  return response.json();
}

