interface ChatMessageProps {
  text: string;
  isUser?: boolean;
  isTyping?: boolean;
}

export default function ChatMessage({ text, isUser, isTyping }: ChatMessageProps) {
  // Special UI for typing indicator
  if (isTyping) {
    return (
      <div className="self-start flex items-center gap-3">
        {/* Profile Picture */}
        <img
          src="/pharmamiku_thinking.png"
          alt="PharmaMiku"
          className="w-16 h-16 rounded-full object-cover flex-shrink-0"
        />
        {/* Thinking Bubble */}
        <div className="bg-[#D1F1F0] text-gray-600 px-6 py-3 rounded-3xl flex gap-2 items-center w-fit thinking-bubble">
          <span className="thinking-text">{text}</span>

          {/* Animated dots with bounce effect */}
          <span className="thinking-dot">.</span>
          <span className="thinking-dot thinking-dot-delay-1">.</span>
          <span className="thinking-dot thinking-dot-delay-2">.</span>
        </div>
      </div>
    );
  }

  // Normal message bubble
  return (
    <div
      className={`max-w-xl px-6 py-4 rounded-3xl whitespace-pre-line leading-relaxed ${
        isUser
          ? "self-end bg-[#FFB7D5] text-white"
          : "self-start bg-[#39C5BB] text-white"
      }`}
    >
      {text}
    </div>
  );
}


