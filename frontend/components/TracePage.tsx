"use client";

import { useState, useEffect } from "react";
import { useTrace, Trace } from "../utils/useTrace";

interface TracePageProps {
  sessionId: string;
  prompt: string;
  onBack: () => void;
}

export default function TracePage({ sessionId, prompt, onBack }: TracePageProps) {
  const { trace, loading, error } = useTrace(sessionId, true);
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
      <div className="h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#39C5BB] mx-auto mb-4"></div>
          <p className="text-gray-600">Loading trace...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">Error: {error}</p>
          <button
            onClick={onBack}
            className="px-4 py-2 bg-[#39C5BB] text-white rounded-lg hover:bg-[#2fa89f] transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  if (!trace || trace.steps.length === 0) {
    return (
      <div className="h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-4">No trace data available</p>
          <button
            onClick={onBack}
            className="px-4 py-2 bg-[#39C5BB] text-white rounded-lg hover:bg-[#2fa89f] transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-gray-50 flex flex-col overflow-hidden">
      <div className="max-w-6xl mx-auto w-full h-full flex flex-col p-6">
        {/* Header with Prompt */}
        <div className="mb-6 flex-shrink-0">
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={onBack}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors flex items-center gap-2"
            >
              <span>←</span>
              <span>Back to Chat</span>
            </button>
          </div>
          
          {/* Prompt Display */}
          <div className="bg-white rounded-lg shadow-lg p-6 border-l-4 border-[#39C5BB]">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-[#39C5BB]/10 flex items-center justify-center">
                <span className="text-[#39C5BB] text-lg">💬</span>
              </div>
              <div className="flex-1">
                <h2 className="text-sm font-semibold text-gray-600 mb-2">User Prompt</h2>
                <p className="text-lg text-gray-800 leading-relaxed">{prompt}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Trace Timeline - Scrollable */}
        <div className="bg-white rounded-lg shadow-lg p-6 flex-1 overflow-y-auto">
          <div className="mb-6 pb-4 border-b border-[#39C5BB]/20">
            <h3 className="text-2xl font-semibold text-gray-800 mb-2">
              <span className="text-[#39C5BB]">🔍</span> Execution Trace
            </h3>
            <div className="flex flex-wrap gap-4 text-sm text-gray-600">
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
          <div className="space-y-4">
            {trace.steps.map((step, index) => {
              const isExpanded = expandedSteps.has(step.step_id);
              const isLast = index === trace.steps.length - 1;

              return (
                <div key={step.step_id} className="relative">
                  {/* Timeline connector */}
                  {!isLast && (
                    <div className="absolute left-6 top-14 w-0.5 h-full bg-[#39C5BB]/30"></div>
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
      </div>
    </div>
  );
}

