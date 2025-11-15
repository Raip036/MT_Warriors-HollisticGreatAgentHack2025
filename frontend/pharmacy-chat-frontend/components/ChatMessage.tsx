interface ChatMessageProps {
  text: string;
  isUser?: boolean;
}

export default function ChatMessage({ text, isUser = false }: ChatMessageProps) {
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} my-2`}>
      <div className={`p-3 rounded-lg max-w-xs ${isUser ? "bg-blue-500 text-white" : "bg-gray-200 text-gray-800"}`}>
        {text}
      </div>
    </div>
  );
}
