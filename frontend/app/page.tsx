"use client";

import { useState, useRef, useEffect } from "react";
import ChatBox from "../components/ChatBox";
import ChatMessage from "../components/ChatMessage";
import TraceView from "../components/TraceView";
import TraceViewer from "../components/TraceViewer";
import { askBackend } from "../utils/api";
import { useTrace } from "../utils/useTrace";

export default function Home() {
  const [messages, setMessages] = useState<
    { text: string; isUser?: boolean; trace?: any; session_id?: string }[]
  >([]);
  const [showTrace, setShowTrace] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  const { trace, loading, error } = useTrace(currentSessionId, showTrace);

  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="min-h-screen bg-[#F3F7FF] flex flex-col items-center relative">

      {/* Pharmamiku Mascot */}
      <img
        src="/pharmamiku.png"
        alt="Pharmamiku"
        className="w-72 fixed bottom-5 left-5 opacity-90 pointer-events-none"
      />

      {/* Title */}
      <div className="text-center mt-10 mb-4">
        <h1 className="text-[44px] font-[400] leading-tight">
          <span className="text-[#39C5BB]">pharma</span>
          <span className="text-[#FFB7D5] font-[600]">miku</span>
        </h1>
        <p className="text-gray-500 text-sm">
          Powered by Amazon Bedrock and Valyu AI.
        </p>
        
        {/* Show Trace Toggle */}
        <div className="mt-4 flex justify-center">
          <button
            onClick={() => {
              setShowTrace(!showTrace);
              // Get the latest session_id from the last message
              const lastMessage = messages
                .filter((m) => !m.isUser && m.session_id)
                .pop();
              if (lastMessage?.session_id) {
                setCurrentSessionId(lastMessage.session_id);
              }
            }}
            className="px-4 py-2 bg-[#39C5BB] text-white rounded-lg hover:bg-[#2fa89f] transition-colors text-sm font-medium flex items-center gap-2"
          >
            <span>🔍</span>
            <span>{showTrace ? "Hide" : "Show"} Agent Trace</span>
          </button>
        </div>
      </div>

      {/* Chat scroll area */}
      <div
        ref={scrollRef}
        className="
          w-full max-w-3xl
          overflow-y-auto
          px-4
          pb-12
          relative
        "
        style={{ height: "calc(100vh - 250px)" }}
      >
        <div className="flex flex-col gap-4">
          {messages.map((m, i) => (
            <div key={i} className="flex flex-col">
              <ChatMessage text={m.text} isUser={m.isUser} />
              {!m.isUser && m.trace && (
                <div className="self-start max-w-xl mt-2">
                  <TraceView trace={m.trace} />
                </div>
              )}
            </div>
          ))}
          
          {/* Trace Viewer */}
          {showTrace && (
            <div className="mt-4 w-full">
              <TraceViewer trace={trace} loading={loading} error={error} />
            </div>
          )}
        </div>
      </div>

      {/* Single fade behind input (correct!) */}
      <div
        className="
          pointer-events-none
          fixed
          bottom-[56px]
          left-0
          w-full
          flex
          justify-center
        "
      >
        <div
          className="
            w-full
            max-w-3xl
            h-12
            bg-gradient-to-t
            from-[#F3F7FF]
            to-transparent
            backdrop-blur-md
          "
        ></div>
      </div>

      {/* Input bar */}
      <div className="fixed bottom-8 w-full flex justify-center">
        <div className="w-full max-w-3xl px-4">
          <ChatBox
            onSend={async (msg) => {
              setMessages((prev) => [...prev, { text: msg, isUser: true }]);

              const typingMessage = {
                text: "pharmamiku is identifying the problem…",
                isUser: false,
                isTyping: true,
              };

              setMessages((prev) => [...prev, typingMessage]);

              const data = await askBackend(msg, (progressMessage) => {
                // Update the typing message with progress
                setMessages((prev) =>
                  prev.map((m) =>
                    m.isTyping
                      ? { ...m, text: progressMessage }
                      : m
                  )
                );
              });

              const finalMessage = {
                text: data.response ?? data.error ?? "No response from agent.",
                isUser: false,
                trace: data.trace || null,
                session_id: data.session_id || null,
              };
              
              setMessages((prev) => [
                ...prev.filter((m) => !m.isTyping),
                finalMessage,
              ]);
              
              // Update current session ID if trace is shown
              if (showTrace && data.session_id) {
                setCurrentSessionId(data.session_id);
              }
            }}
          />
        </div>
      </div>
    </div>
  );
}
