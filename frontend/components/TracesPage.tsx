"use client";

import { useState, useEffect, useMemo } from "react";
import TraceViewer from "./TraceViewer";
import { Trace } from "../utils/useTrace";

interface Message {
  text: string;
  isUser?: boolean;
  trace?: any;
  session_id?: string;
}

interface TracesPageProps {
  messages: Message[];
  onBack: () => void;
}

export default function TracesPage({ messages, onBack }: TracesPageProps) {
  const [traces, setTraces] = useState<Map<string, { trace: Trace | null; loading: boolean; error: string | null }>>(new Map());
  
  // Extract all user prompts with their corresponding AI responses
  const prompts = useMemo(() => {
    return messages
      .map((msg, index) => {
        if (msg.isUser) {
          // Find the corresponding AI response (next non-user message)
          const aiResponse = messages.slice(index + 1).find(m => !m.isUser && !m.isTyping);
          return {
            prompt: msg.text,
            response: aiResponse?.text || "",
            sessionId: aiResponse?.session_id || null,
            timestamp: index, // Use index as a simple identifier
          };
        }
        return null;
      })
      .filter((p): p is NonNullable<typeof p> => p !== null && p.sessionId !== null);
  }, [messages]);

  // Fetch traces for all prompts
  useEffect(() => {
    if (prompts.length === 0) return;
    
    const fetchAllTraces = async () => {
      // Set loading state for all prompts
      const loadingMap = new Map();
      prompts.forEach((prompt) => {
        if (prompt.sessionId) {
          loadingMap.set(prompt.sessionId, { trace: null, loading: true, error: null });
        }
      });
      setTraces(loadingMap);

      const tracePromises = prompts.map(async (prompt) => {
        if (!prompt.sessionId) return null;
        
        try {
          const response = await fetch(`http://localhost:8000/trace/${prompt.sessionId}`);
          if (!response.ok) {
            if (response.status === 404) {
              return { trace: null, loading: false, error: null };
            }
            throw new Error(`Failed to fetch trace: ${response.statusText}`);
          }
          const data = await response.json();
          return { trace: data, loading: false, error: null };
        } catch (err) {
          return { 
            trace: null, 
            loading: false, 
            error: err instanceof Error ? err.message : "Failed to fetch trace" 
          };
        }
      });

      const results = await Promise.all(tracePromises);
      const tracesMap = new Map();
      prompts.forEach((prompt, index) => {
        if (prompt.sessionId) {
          tracesMap.set(prompt.sessionId, results[index] || { trace: null, loading: false, error: null });
        }
      });
      setTraces(tracesMap);
    };

    fetchAllTraces();
  }, [prompts]); // Re-fetch when prompts change

  return (
    <div className="h-screen bg-gray-100 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <svg
              className="w-6 h-6 text-gray-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
          </button>
          <div>
            <h1 className="text-2xl font-semibold text-gray-800">
              <span className="text-[#39C5BB]">Agent</span>{" "}
              <span className="text-[#FFB7D5]">Traces</span>
            </h1>
            <p className="text-sm text-gray-500">
              View execution traces for all prompts in this session
            </p>
          </div>
        </div>
        <div className="text-sm text-gray-500">
          {prompts.length} {prompts.length === 1 ? "prompt" : "prompts"}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {prompts.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <p className="text-gray-400 text-lg mb-2">No traces available</p>
              <p className="text-gray-300 text-sm">
                Start a conversation to see agent traces
              </p>
            </div>
          </div>
        ) : (
          <div className="max-w-6xl mx-auto space-y-8">
            {prompts.map((prompt, index) => {
              const traceData = prompt.sessionId ? traces.get(prompt.sessionId) : null;
              const isLoading = traceData?.loading ?? true;
              const trace = traceData?.trace ?? null;
              const error = traceData?.error ?? null;

              return (
                <div
                  key={`${prompt.sessionId}-${index}`}
                  className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
                >
                  {/* Prompt Header */}
                  <div className="bg-gradient-to-r from-[#39C5BB]/10 to-[#FFB7D5]/10 px-6 py-4 border-b border-gray-200">
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-[#39C5BB] text-white flex items-center justify-center font-semibold text-lg">
                        {index + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-lg font-semibold text-gray-800 mb-2">
                          Prompt
                        </h3>
                        <p className="text-gray-700 whitespace-pre-wrap break-words">
                          {prompt.prompt}
                        </p>
                        {prompt.response && (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <h4 className="text-sm font-medium text-gray-600 mb-1">
                              Response Preview:
                            </h4>
                            <p className="text-sm text-gray-500 line-clamp-2">
                              {prompt.response}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Trace Content */}
                  <div className="p-6">
                    {isLoading ? (
                      <div className="flex items-center justify-center py-12">
                        <div className="text-center">
                          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-[#39C5BB] mb-4"></div>
                          <p className="text-sm text-gray-500">Loading trace...</p>
                        </div>
                      </div>
                    ) : error ? (
                      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                        <p className="text-sm text-red-600">
                          Error loading trace: {error}
                        </p>
                      </div>
                    ) : trace ? (
                      <TraceViewer trace={trace} loading={false} error={null} />
                    ) : (
                      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                        <p className="text-sm text-gray-500 text-center">
                          Trace not available for this prompt
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

