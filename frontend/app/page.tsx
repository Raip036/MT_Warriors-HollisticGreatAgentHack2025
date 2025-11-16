"use client";

import { useState, useRef, useEffect } from "react";
import ChatBox from "../components/ChatBox";
import ChatMessage from "../components/ChatMessage";
import TraceView from "../components/TraceView";
import TraceViewer from "../components/TraceViewer";
import Sidebar from "../components/Sidebar";
import { askBackend } from "../utils/api";
import { useTrace } from "../utils/useTrace";

interface ChatSession {
  id: string;
  title: string;
  timestamp: Date;
  messages: { text: string; isUser?: boolean; trace?: any; isTyping?: boolean; session_id?: string }[];
}

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<
    { text: string; isUser?: boolean; trace?: any; session_id?: string; isTyping?: boolean }[]
  >([]);
  const [showTrace, setShowTrace] = useState(false);
  const [traceSessionId, setTraceSessionId] = useState<string | null>(null);

  const { trace, loading, error } = useTrace(traceSessionId, showTrace);

  const scrollRef = useRef<HTMLDivElement>(null);

  // Load chat history from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("pharmamiku_chat_sessions");
    if (saved) {
      try {
        const sessions = JSON.parse(saved).map((s: any) => ({
          ...s,
          timestamp: new Date(s.timestamp),
        }));
        setChatSessions(sessions);
      } catch (e) {
        console.error("Error loading chat history:", e);
      }
    }
  }, []);

  // Save chat sessions to localStorage whenever they change
  useEffect(() => {
    if (chatSessions.length > 0) {
      localStorage.setItem(
        "pharmamiku_chat_sessions",
        JSON.stringify(chatSessions)
      );
    }
  }, [chatSessions]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Generate session title from first user message
  const generateSessionTitle = (firstMessage: string): string => {
    if (firstMessage.length > 30) {
      return firstMessage.substring(0, 30) + "...";
    }
    return firstMessage;
  };

  // Start a new chat session
  const handleNewChat = () => {
    setCurrentSessionId(null);
    setMessages([]);
    setSidebarOpen(false);
    setShowTrace(false);
    setTraceSessionId(null);
  };

  // Select an existing chat session
  const handleSelectSession = (session: ChatSession) => {
    setCurrentSessionId(session.id);
    setMessages(session.messages);
    setSidebarOpen(false);
    // Extract session_id from the last message if available
    const lastMessage = session.messages
      .filter((m) => !m.isUser && m.session_id)
      .pop();
    if (lastMessage?.session_id) {
      setTraceSessionId(lastMessage.session_id);
    }
  };

  // Save current session
  const saveCurrentSession = () => {
    if (messages.length === 0) return;

    const userMessages = messages.filter((m) => m.isUser);
    if (userMessages.length === 0) return;

    const title = generateSessionTitle(userMessages[0].text);
    const sessionId = currentSessionId || `session_${Date.now()}`;

    const session: ChatSession = {
      id: sessionId,
      title,
      timestamp: currentSessionId
        ? chatSessions.find((s) => s.id === currentSessionId)?.timestamp ||
          new Date()
        : new Date(),
      messages: messages.filter((m) => !m.isTyping), // Don't save typing indicators
    };

    if (currentSessionId) {
      // Update existing session
      setChatSessions((prev) =>
        prev.map((s) => (s.id === currentSessionId ? session : s))
      );
    } else {
      // Create new session
      setChatSessions((prev) => [session, ...prev]);
      setCurrentSessionId(sessionId);
    }
  };

  // Handle sending a message
  const handleSend = async (msg: string) => {
    // If this is a new chat, create a new session
    if (!currentSessionId) {
      const newSessionId = `session_${Date.now()}`;
      setCurrentSessionId(newSessionId);
    }

    // Add user message
    setMessages((prev) => [...prev, { text: msg, isUser: true }]);

    // Add typing indicator
    const typingMessage = {
      text: "pharmamiku is identifying the problem…",
      isUser: false,
      isTyping: true,
    };

    setMessages((prev) => [...prev, typingMessage]);

    try {
      const data = await askBackend(msg, (progressMessage) => {
        // Update the typing message with progress
        setMessages((prev) =>
          prev.map((m) =>
            m.isTyping ? { ...m, text: progressMessage } : m
          )
        );
      });

      // Replace typing indicator with actual response
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

      // Update trace session ID if available
      if (data.session_id) {
        setTraceSessionId(data.session_id);
      }

      // Auto-save after a short delay
      setTimeout(() => {
        saveCurrentSession();
      }, 500);
    } catch (error) {
      // Remove typing indicator on error
      setMessages((prev) => prev.filter((m) => !m.isTyping));
      setMessages((prev) => [
        ...prev,
        {
          text: "Sorry, I encountered an error. Please try again.",
          isUser: false,
        },
      ]);
    }
  };

  return (
    <div className="min-h-screen bg-[#F3F7FF] flex flex-col items-center relative">
      {/* Pharmamiku Mascot */}
      <img
        src="/pharmamiku.png"
        alt="Pharmamiku"
        className="w-72 fixed bottom-5 left-5 opacity-90 pointer-events-none"
      />

      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        chatSessions={chatSessions}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        currentSessionId={currentSessionId}
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
                setTraceSessionId(lastMessage.session_id);
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
              {!m.isUser && !m.isTyping && m.trace && (
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
          <ChatBox onSend={handleSend} />
        </div>
      </div>
    </div>
  );
}
