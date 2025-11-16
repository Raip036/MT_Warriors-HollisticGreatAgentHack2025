"use client";

import { useState, useRef, useEffect } from "react";
import ChatBox from "../components/ChatBox";
import ChatMessage from "../components/ChatMessage";
import TraceView from "../components/TraceView";
import TraceViewer from "../components/TraceViewer";
import Sidebar from "../components/Sidebar";
import InsightsPage from "../components/InsightsPage";
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
    { text: string; isUser?: boolean; trace?: any; isTyping?: boolean; session_id?: string }[]
  >([]);
  const [showTrace, setShowTrace] = useState(false);
  const [traceSessionId, setTraceSessionId] = useState<string | null>(null);
  const [showInsights, setShowInsights] = useState(false);

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
    // Save current session before clearing (if there are messages)
    if (messages.length > 0) {
      const userMessages = messages.filter((m) => m.isUser);
      if (userMessages.length > 0) {
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

        let updatedSessions: ChatSession[];
        if (currentSessionId) {
          // Update existing session
          updatedSessions = chatSessions.map((s) => (s.id === currentSessionId ? session : s));
        } else {
          // Create new session
          updatedSessions = [session, ...chatSessions];
        }

        // Update state
        setChatSessions(updatedSessions);
        
        // Immediately save to localStorage
        localStorage.setItem(
          "pharmamiku_chat_sessions",
          JSON.stringify(updatedSessions)
        );
      }
    }

    // Now clear for new chat
    setCurrentSessionId(null);
    setMessages([]);
    // Don't close sidebar - only X button should close it
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

    let updatedSessions: ChatSession[];
    if (currentSessionId) {
      // Update existing session
      updatedSessions = chatSessions.map((s) => (s.id === currentSessionId ? session : s));
    } else {
      // Create new session
      updatedSessions = [session, ...chatSessions];
      setCurrentSessionId(sessionId);
    }

    // Update state
    setChatSessions(updatedSessions);
    
    // Immediately save to localStorage
    localStorage.setItem(
      "pharmamiku_chat_sessions",
      JSON.stringify(updatedSessions)
    );
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
      text: "pharmamiku is identifying the problem",
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
        session_id: data.session_id || undefined,
      };

      setMessages((prev) => [
        ...prev.filter((m) => !m.isTyping),
        finalMessage,
      ]);

      // Update trace session ID if available
      if (data.session_id) {
        setTraceSessionId(data.session_id);
      } else {
        setTraceSessionId(null);
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

  // Show insights page if requested
  if (showInsights) {
    return <InsightsPage onBack={() => setShowInsights(false)} />;
  }

  return (
    <div className="h-screen bg-gray-100 flex overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        chatSessions={chatSessions}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        currentSessionId={currentSessionId}
        onShowInsights={() => setShowInsights(true)}
        onShowTrace={() => {
          setShowTrace(!showTrace);
          // Get the latest session_id from the last message
          const lastMessage = messages
            .filter((m) => !m.isUser && m.session_id)
            .pop();
          if (lastMessage?.session_id) {
            setTraceSessionId(lastMessage.session_id);
          }
        }}
        hasMessages={messages.length > 0}
      />

      {/* Main Content Area */}
      <div
        className={`flex-1 transition-all duration-300 overflow-hidden flex ${
          sidebarOpen ? "md:ml-64" : "ml-0"
        }`}
      >
        <div className="w-full h-full flex flex-col bg-white md:rounded-lg md:m-4 md:shadow-lg md:border md:border-gray-200 md:max-h-[calc(100vh-2rem)]">
          {/* Header */}
          <div className="text-center py-8 border-b border-gray-100">
            <h1 className="text-[44px] font-[400] leading-tight mb-2">
              <span className="text-[#39C5BB]">pharma</span>
              <span className="text-[#FFB7D5] font-[600]">miku</span>
            </h1>
            <p className="text-gray-500 text-sm">
              Powered by Amazon Bedrock and Valyu AI.
            </p>
          </div>

          {/* Chat Area */}
          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto px-6 py-4 relative"
          >
            {messages.length === 0 ? (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <p className="text-gray-400 text-lg mb-2">
                    Start a conversation with PharmaMiku
                  </p>
                  <p className="text-gray-300 text-sm">
                    Ask me anything about medications and healthcare!
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex flex-col gap-4">
                {messages.map((m, i) => (
                  <div key={i} className="flex flex-col">
                    <ChatMessage text={m.text} isUser={m.isUser} isTyping={m.isTyping} />
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
            )}
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-100 p-4">
            <ChatBox onSend={handleSend} />
            <p className="text-xs text-gray-400 text-center mt-2">
              Not medical advice.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
