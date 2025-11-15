import { useState } from "react";

interface ChatBoxProps {
  onSend: (message: string) => void;
}

export default function ChatBox({ onSend }: ChatBoxProps) {
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;
    onSend(input);
    setInput("");
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSend();
  };

  return (
    <div className="flex mt-4">
      <input
        type="text"
        className="flex-1 p-3 rounded-l-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
        placeholder="Type your question..."
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyPress}
      />
      <button
        className="bg-blue-500 text-white px-4 rounded-r-lg hover:bg-blue-600"
        onClick={handleSend}
      >
        Send
      </button>
    </div>
  );
}
