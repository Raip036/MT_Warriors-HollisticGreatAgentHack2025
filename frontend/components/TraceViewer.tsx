"use client";

import { useState } from "react";
import { Trace, TraceStep } from "../utils/useTrace";

interface TraceViewerProps {
  trace: Trace | null;
  loading: boolean;
  error: string | null;
}

export default function TraceViewer({ trace, loading, error }: TraceViewerProps) {
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());

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
        return "bg-[#F3F7FF] text-gray-700 border-gray-300";
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

  if (loading) {
    return (
      <div className="p-4 bg-white rounded-lg border border-[#39C5BB]/20">
        <p className="text-sm text-[#39C5BB]">Loading trace...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 rounded-lg border border-red-200">
        <p className="text-sm text-red-600">Error loading trace: {error}</p>
      </div>
    );
  }

  if (!trace || trace.steps.length === 0) {
    return (
      <div className="p-4 bg-[#F3F7FF] rounded-lg border border-[#39C5BB]/20">
        <p className="text-sm text-gray-500">No trace data available</p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-4xl mx-auto p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
      {/* Header */}
      <div className="mb-4 pb-4 border-b border-[#39C5BB]/20">
        <h3 className="text-lg font-semibold text-gray-800 mb-2">
          <span className="text-[#39C5BB]">🔍</span> Agent Trace Timeline
        </h3>
        <div className="flex flex-wrap gap-4 text-xs text-gray-600">
          <span>
            <strong>Session:</strong> {trace.session_id.slice(0, 8)}...
          </span>
          <span>
            <strong>Total Steps:</strong> {trace.metadata.total_steps}
          </span>
          <span>
            <strong>Tool Calls:</strong> {trace.metadata.total_tool_calls}
          </span>
          <span>
            <strong>Decisions:</strong> {trace.metadata.total_decisions}
          </span>
          {trace.metadata.duration_seconds && (
            <span>
              <strong>Duration:</strong> {trace.metadata.duration_seconds.toFixed(2)}s
            </span>
          )}
        </div>
      </div>

      {/* Steps Timeline */}
      <div className="space-y-3">
        {trace.steps.map((step, index) => {
          const isExpanded = expandedSteps.has(step.step_id);
          const isLast = index === trace.steps.length - 1;

          return (
            <div key={step.step_id} className="relative">
              {/* Timeline connector */}
              {!isLast && (
                <div className="absolute left-6 top-12 w-0.5 h-full bg-[#39C5BB]/30"></div>
              )}

              {/* Step Card */}
              <div
                className={`relative bg-white rounded-lg border-2 ${getStepTypeColor(
                  step.type
                )} transition-all hover:shadow-md`}
              >
                {/* Step Header */}
                <button
                  onClick={() => toggleStep(step.step_id)}
                  className="w-full p-4 flex items-start gap-4 text-left"
                >
                  {/* Step Number & Icon */}
                  <div className="flex-shrink-0 w-12 h-12 rounded-full bg-white border-2 border-current flex items-center justify-center font-semibold text-sm">
                    <span className="text-lg">{getStepTypeIcon(step.type)}</span>
                  </div>

                  {/* Step Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-sm">
                        Step {step.step_id}
                      </span>
                      <span className="px-2 py-0.5 rounded text-xs font-medium bg-current/20">
                        {step.type.replace("_", " ")}
                      </span>
                      {step.tool_name && (
                        <span className="px-2 py-0.5 rounded text-xs bg-white/50">
                          {step.tool_name}
                        </span>
                      )}
                      {step.success === false && (
                        <span className="px-2 py-0.5 rounded text-xs bg-red-500 text-white">
                          Failed
                        </span>
                      )}
                    </div>

                    {/* Summary */}
                    {step.metadata?.summary && (
                      <p className="text-sm text-gray-700 mb-1 line-clamp-2">
                        {step.metadata.summary}
                      </p>
                    )}

                    {/* Metadata */}
                    <div className="flex flex-wrap gap-2 text-xs text-gray-600">
                      {step.metadata?.agent && (
                        <span>Agent: {step.metadata.agent}</span>
                      )}
                      {step.duration_ms !== undefined && (
                        <span>Duration: {step.duration_ms.toFixed(0)}ms</span>
                      )}
                      <span>
                        {new Date(step.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>

                  {/* Expand/Collapse Icon */}
                  <div className="flex-shrink-0">
                    <svg
                      className={`w-5 h-5 transition-transform ${
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

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="px-4 pb-4 border-t border-current/20 pt-4 space-y-4">
                    {/* Input */}
                    <div>
                      <h4 className="font-semibold text-sm mb-2">Input:</h4>
                      <pre className="text-xs bg-white/50 p-3 rounded overflow-x-auto max-h-48 overflow-y-auto">
                        {JSON.stringify(step.input, null, 2)}
                      </pre>
                    </div>

                    {/* Output */}
                    <div>
                      <h4 className="font-semibold text-sm mb-2">Output:</h4>
                      <pre className="text-xs bg-white/50 p-3 rounded overflow-x-auto max-h-48 overflow-y-auto">
                        {JSON.stringify(step.output, null, 2)}
                      </pre>
                    </div>

                    {/* Error */}
                    {step.error && (
                      <div className="bg-red-50 border border-red-200 rounded p-3">
                        <h4 className="font-semibold text-sm text-red-800 mb-1">
                          Error:
                        </h4>
                        <p className="text-xs text-red-600">{step.error}</p>
                      </div>
                    )}

                    {/* Full Metadata */}
                    {step.metadata && Object.keys(step.metadata).length > 0 && (
                      <div>
                        <h4 className="font-semibold text-sm mb-2">Metadata:</h4>
                        <pre className="text-xs bg-white/50 p-3 rounded overflow-x-auto max-h-32 overflow-y-auto">
                          {JSON.stringify(step.metadata, null, 2)}
                        </pre>
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

