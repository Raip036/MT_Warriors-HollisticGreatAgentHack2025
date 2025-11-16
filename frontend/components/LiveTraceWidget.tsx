"use client";

import { useState, useEffect } from "react";
import { FiX, FiFilter, FiRefreshCw } from "react-icons/fi";

const BACKEND_URL = "http://localhost:8000";

interface TraceStep {
  step_id: number;
  type: string;
  timestamp: string;
  input?: any;
  output?: any;
  metadata?: any;
  tool_name?: string;
  duration_ms?: number;
  success?: boolean;
  error?: string;
}

interface LiveTraceWidgetProps {
  sessionId: string | null;
  onClose?: () => void;
}

export default function LiveTraceWidget({ sessionId, onClose }: LiveTraceWidgetProps) {
  const [trace, setTrace] = useState<{ steps: TraceStep[]; metadata?: any } | null>(null);
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());
  const [filterType, setFilterType] = useState<string>("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Poll for trace updates
  useEffect(() => {
    if (!sessionId || !autoRefresh) return;

    const fetchTrace = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/trace/${sessionId}`);
        if (!response.ok) {
          if (response.status === 404) {
            // Trace not ready yet, that's okay
            return;
          }
          throw new Error(`Failed to load trace: ${response.status}`);
        }
        const data = await response.json();
        setTrace(data);
        setError(null);
      } catch (err: any) {
        if (err.message !== "Failed to load trace: 404") {
          setError(err.message);
        }
      }
    };

    // Initial fetch
    fetchTrace();

    // Poll every 500ms for live updates
    const interval = setInterval(fetchTrace, 500);

    return () => clearInterval(interval);
  }, [sessionId, autoRefresh]);

  const toggleStep = (stepId: number) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(stepId)) {
      newExpanded.delete(stepId);
    } else {
      newExpanded.add(stepId);
    }
    setExpandedSteps(newExpanded);
  };

  const getStepTypeColor = (type: string) => {
    switch (type) {
      case "decision":
        return "bg-[#39C5BB]/10 text-[#39C5BB] border-[#39C5BB]/30";
      case "tool_call":
        return "bg-[#FFB7D5]/10 text-[#FFB7D5] border-[#FFB7D5]/30";
      case "memory_update":
        return "bg-[#39C5BB]/20 text-[#2fa89f] border-[#39C5BB]/40";
      case "state_transition":
        return "bg-[#FFB7D5]/20 text-[#e6a5c4] border-[#FFB7D5]/40";
      default:
        return "bg-gray-100 text-gray-700 border-gray-300";
    }
  };

  const getStepTypeIcon = (type: string) => {
    switch (type) {
      case "decision":
        return "🧠";
      case "tool_call":
        return "🔧";
      case "memory_update":
        return "💾";
      case "state_transition":
        return "🔄";
      default:
        return "📝";
    }
  };

  // Filter steps
  const filteredSteps = trace?.steps.filter((step) => {
    if (filterType === "all") return true;
    return step.type === filterType;
  }) || [];

  if (!sessionId) {
    return (
      <div className="w-80 bg-white border-l border-gray-200 p-4">
        <p className="text-sm text-gray-500">No active session</p>
      </div>
    );
  }

  return (
    <div className="w-80 bg-white border-l border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gray-800">Live Trace</h3>
          <p className="text-xs text-gray-500">
            {trace?.steps.length || 0} steps
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`p-1.5 rounded ${
              autoRefresh ? "bg-[#39C5BB]/20 text-[#39C5BB]" : "bg-gray-100 text-gray-600"
            }`}
            title={autoRefresh ? "Auto-refresh on" : "Auto-refresh off"}
          >
            <FiRefreshCw className={`w-4 h-4 ${autoRefresh ? "animate-spin" : ""}`} />
          </button>
          {onClose && (
            <button onClick={onClose} className="p-1.5 hover:bg-gray-100 rounded">
              <FiX className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Filter */}
      <div className="p-3 border-b border-gray-200">
        <div className="flex items-center gap-2 mb-2">
          <FiFilter className="w-4 h-4 text-gray-500" />
          <span className="text-xs font-medium text-gray-700">Filter:</span>
        </div>
        <div className="flex flex-wrap gap-1">
          {["all", "decision", "tool_call", "memory_update"].map((type) => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              className={`px-2 py-1 rounded text-xs transition-colors ${
                filterType === type
                  ? "bg-[#39C5BB] text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {type.replace("_", " ")}
            </button>
          ))}
        </div>
      </div>

      {/* Trace Steps */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded p-2 mb-2">
            <p className="text-xs text-red-600">{error}</p>
          </div>
        )}

        {loading && !trace && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[#39C5BB] mx-auto mb-2"></div>
            <p className="text-xs text-gray-500">Loading trace...</p>
          </div>
        )}

        {!trace && !loading && (
          <div className="text-center py-8">
            <p className="text-xs text-gray-500">Trace will appear here as agent executes</p>
          </div>
        )}

        {filteredSteps.length === 0 && trace && (
          <div className="text-center py-8">
            <p className="text-xs text-gray-500">No {filterType === "all" ? "" : filterType} steps yet</p>
          </div>
        )}

        {filteredSteps.map((step, index) => {
          const isExpanded = expandedSteps.has(step.step_id);
          const isLast = index === filteredSteps.length - 1;

          return (
            <div key={step.step_id ?? `step-${index}`} className="relative">
              {!isLast && (
                <div className="absolute left-4 top-10 w-0.5 h-full bg-[#39C5BB]/30"></div>
              )}

              <div
                className={`relative bg-white rounded-lg border-2 ${getStepTypeColor(
                  step.type ?? "unknown"
                )} transition-all hover:shadow-sm`}
              >
                <button
                  onClick={() => toggleStep(step.step_id ?? index)}
                  className="w-full p-2 flex items-start gap-2 text-left"
                >
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-white border-2 border-current flex items-center justify-center text-xs">
                    <span>{getStepTypeIcon(step.type ?? "unknown")}</span>
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1 mb-0.5">
                      <span className="font-semibold text-xs">
                        #{step.step_id ?? index + 1}
                      </span>
                      <span className="px-1.5 py-0.5 rounded text-xs font-medium bg-current/20">
                        {(step.type ?? "unknown").replace("_", " ")}
                      </span>
                      {step.tool_name && (
                        <span className="px-1.5 py-0.5 rounded text-xs bg-white/50 truncate max-w-[80px]">
                          {step.tool_name}
                        </span>
                      )}
                      {step.success === false && (
                        <span className="px-1.5 py-0.5 rounded text-xs bg-red-500 text-white">
                          ✗
                        </span>
                      )}
                    </div>

                    {step.metadata?.summary && (
                      <p className="text-xs text-gray-700 line-clamp-1 mb-0.5">
                        {step.metadata.summary}
                      </p>
                    )}

                    <div className="flex flex-wrap gap-1 text-xs text-gray-500">
                      {step.duration_ms !== undefined && (
                        <span>{step.duration_ms.toFixed(0)}ms</span>
                      )}
                      {step.timestamp && (
                        <span>
                          {new Date(step.timestamp).toLocaleTimeString()}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex-shrink-0">
                    <svg
                      className={`w-3 h-3 transition-transform ${
                        isExpanded ? "rotate-180" : ""
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 9l-7 7-7-7"
                      />
                    </svg>
                  </div>
                </button>

                {isExpanded && (
                  <div className="px-2 pb-2 border-t border-current/20 pt-2 space-y-2 text-xs">
                    {step.input !== undefined && (
                      <div>
                        <h4 className="font-semibold text-xs mb-1">Input:</h4>
                        <pre className="text-xs bg-white/50 p-2 rounded overflow-x-auto max-h-32 overflow-y-auto">
                          {JSON.stringify(step.input, null, 2)}
                        </pre>
                      </div>
                    )}

                    {step.output !== undefined && (
                      <div>
                        <h4 className="font-semibold text-xs mb-1">Output:</h4>
                        <pre className="text-xs bg-white/50 p-2 rounded overflow-x-auto max-h-32 overflow-y-auto">
                          {JSON.stringify(step.output, null, 2)}
                        </pre>
                      </div>
                    )}

                    {step.error && (
                      <div className="bg-red-50 border border-red-200 rounded p-2">
                        <h4 className="font-semibold text-xs text-red-800 mb-1">Error:</h4>
                        <p className="text-xs text-red-600">{step.error}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

