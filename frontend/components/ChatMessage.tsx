interface ChatMessageProps {
  text: string;
  isUser?: boolean;
  isTyping?: boolean;
}

export default function ChatMessage({ text, isUser, isTyping }: ChatMessageProps) {
  // Special UI for typing indicator
  if (isTyping) {
    return (
      <div className="self-start bg-[#D1F1F0] text-gray-600 px-6 py-3 rounded-2xl flex gap-2 items-center w-fit thinking-bubble">
        <span className="thinking-text">{text}</span>

        {/* Animated dots with bounce effect */}
        <span className="thinking-dot">.</span>
        <span className="thinking-dot thinking-dot-delay-1">.</span>
        <span className="thinking-dot thinking-dot-delay-2">.</span>
      </div>
    );
  }

  // Normal message bubble
  return (
    <div
      className={`max-w-xl px-6 py-4 rounded-2xl whitespace-pre-line leading-relaxed ${
        isUser
          ? "self-end bg-[#FFB7D5] text-white"
          : "self-start bg-[#39C5BB] text-white"
      }`}
    >
      {text}
    </div>
  );
}


