interface ChatMessageProps {
  text: string;
  isUser?: boolean;
  isTyping?: boolean;
}

export default function ChatMessage({ text, isUser, isTyping }: ChatMessageProps) {
  // Special UI for typing indicator
  if (isTyping) {
    return (
      <div className="self-start bg-[#D1F1F0] text-gray-600 px-6 py-3 rounded-2xl opacity-70 flex gap-2 items-center w-fit">
        <span>pharmamiku is thinking</span>

        {/* Animated dots */}
        <span className="animate-pulse">.</span>
        <span className="animate-pulse delay-150">.</span>
        <span className="animate-pulse delay-300">.</span>
      </div>
    );
  }

  // Normal message bubble
  return (
    <div
      className={`max-w-xl px-6 py-4 rounded-2xl ${
        isUser
          ? "self-end bg-[#FFB7D5] text-white"
          : "self-start bg-[#39C5BB] text-white"
      }`}
    >
      {text}
    </div>
  );
}


