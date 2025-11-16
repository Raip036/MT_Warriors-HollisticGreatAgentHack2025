"use client";

import { useState, useEffect } from "react";

interface ChatSession {
  id: string;
  title: string;
  timestamp: Date;
  messages: any[];
}

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  chatSessions: ChatSession[];
  onSelectSession: (session: ChatSession) => void;
  onNewChat: () => void;
  currentSessionId: string | null;
}

export default function Sidebar({
  isOpen,
  onToggle,
  chatSessions,
  onSelectSession,
  onNewChat,
  currentSessionId,
}: SidebarProps) {
  return (
    <>
      {/* Sidebar */}
      <div
        className={`fixed left-0 top-0 h-full bg-[#D1F1F0] transition-all duration-300 z-40 ${
          isOpen ? "w-64" : "w-0"
        } overflow-hidden`}
      >
        <div className="h-full flex flex-col p-4">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <img
                src="/logo.png"
                alt="Logo"
                className="w-10 h-10 object-contain"
              />
            </div>
            <button
              onClick={onToggle}
              className="text-gray-600 hover:text-gray-800 transition-colors"
            >
              ✕
            </button>
          </div>

          {/* New Chat Button */}
          <button
            onClick={onNewChat}
            className="w-full bg-[#39C5BB] text-white py-2 px-4 rounded-lg hover:bg-[#2FA89A] transition-colors mb-4 text-sm font-medium"
          >
            + New Chat
          </button>

          {/* Chat History */}
          <div className="flex-1 overflow-y-auto sidebar-scroll">
            <h3 className="text-xs font-semibold text-gray-600 mb-2 uppercase tracking-wide">
              Chat History
            </h3>
            <div className="space-y-1">
              {chatSessions.length === 0 ? (
                <p className="text-xs text-gray-500 italic py-4">
                  No chat history yet
                </p>
              ) : (
                chatSessions.map((session) => (
                  <button
                    key={session.id}
                    onClick={() => onSelectSession(session)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                      currentSessionId === session.id
                        ? "bg-[#39C5BB] text-white"
                        : "bg-white/50 text-gray-700 hover:bg-white/70"
                    }`}
                  >
                    <div className="truncate font-medium">{session.title}</div>
                    <div className="text-xs opacity-70 mt-1">
                      {new Date(session.timestamp).toLocaleDateString()}
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* PharmaMiku Image */}
          <div className="flex justify-center pt-4 pb-2">
            <img
              src="/pharmamiku.png"
              alt="PharmaMiku"
              className="w-56 h-56 object-contain opacity-90"
            />
          </div>

          {/* User Info */}
          <div className="flex items-center gap-2 pt-2 border-t border-gray-300">
            <div className="w-8 h-8 rounded-full bg-gray-300"></div>
            <span className="text-sm text-gray-600">Nyree Marsh</span>
          </div>
        </div>
      </div>

      {/* Toggle Button (when sidebar is closed) */}
      {!isOpen && (
        <button
          onClick={onToggle}
          className="fixed left-4 top-4 z-50 w-10 h-10 bg-[#D1F1F0] rounded-lg flex items-center justify-center hover:bg-[#B8E5E2] transition-colors shadow-md"
        >
          <span className="text-gray-700">☰</span>
        </button>
      )}

      {/* Overlay (when sidebar is open on mobile) */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 z-30 md:hidden"
          onClick={onToggle}
        ></div>
      )}
    </>
  );
}

