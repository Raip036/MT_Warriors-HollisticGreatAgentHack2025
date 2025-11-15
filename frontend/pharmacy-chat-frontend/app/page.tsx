"use client";

import { useState } from "react";
import ChatBox from "../components/ChatBox";
import ChatMessage from "../components/ChatMessage";
import { askBackend } from "../utils/api";

export default function Home() {
  const [messages, setMessages] = useState<{ text: string; isUser?: boolean }[]>([]);

  const sendMessage = async (msg: string) => {
    setMessages((prev) => [...prev, { text: msg, isUser: true }]);
    const res = await askBackend(msg);
    const botReply = res.response || res.error || "No response.";
    setMessages((prev) => [...prev, { text: botReply }]);
  };

  return (
    <div className="max-w-2xl mx-auto p-4 flex flex-col h-screen">
      <h1 className="text-2xl font-bold text-center mb-4">Pharmacy Chatbot 💊</h1>
      <div className="flex-1 overflow-y-auto mb-4 p-2 bg-white rounded shadow">
        {messages.map((m, idx) => (
          <ChatMessage key={idx} text={m.text} isUser={m.isUser} />
        ))}
      </div>
      <ChatBox onSend={sendMessage} />
    </div>
  );
}
