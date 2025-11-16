import { useState } from "react";
import { FiArrowRight } from "react-icons/fi";  // Install: npm install react-icons

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
    <div className="flex items-center w-full bg-[#F3F7FF] border border-gray-300 rounded-full px-6 py-3">
      <input
        type="text"
        className="flex-1 bg-transparent text-[#4D4D4D] placeholder:text-gray-400 focus:outline-none text-base"
        placeholder="Hi, I am pharmamiku, how can I help you today?"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyPress}
      />
      <button
        onClick={handleSend}
        className="ml-2 p-2 rounded-full hover:bg-[#FFB7D5] transition flex items-center justify-center"
      >
        <FiArrowRight className="text-gray-600 text-xl" />
      </button>
    </div>
  );
}

