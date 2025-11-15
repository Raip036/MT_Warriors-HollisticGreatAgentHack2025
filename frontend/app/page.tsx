"use client";

import { useState, useRef, useEffect } from "react";
import ChatBox from "../components/ChatBox";
import ChatMessage from "../components/ChatMessage";
import { askBackend } from "../utils/api";

export default function Home() {
  const [messages, setMessages] = useState<
    { text: string; isUser?: boolean }[]
  >([]);

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
            <ChatMessage key={i} text={m.text} isUser={m.isUser} />
          ))}
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
                text: "pharmamiku is thinking…",
                isUser: false,
                isTyping: true,
              };

              setMessages((prev) => [...prev, typingMessage]);

              const data = await askBackend(msg);

              setMessages((prev) => [
                ...prev.filter((m) => !m.isTyping),
                {
                  text: data.response ?? data.error ?? "No response.",
                  isUser: false,
                },
              ]);
            }}
          />
        </div>
      </div>
    </div>
  );
}
