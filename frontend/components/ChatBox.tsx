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
    <div className="flex items-center gap-3 w-full">
      {/* Input field */}
      <div className="flex-1 flex items-center bg-[#F3F7FF] border border-gray-300 rounded-full px-6 py-3">
        <input
          type="text"
          className="flex-1 bg-transparent text-[#4D4D4D] placeholder:text-gray-400 focus:outline-none text-lg"
          placeholder="Hi, I am pharmamiku, how can I help you today?"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
        />
      </div>

      {/* Send button */}
      <button
        onClick={handleSend}
        className="p-3 rounded-xl border border-gray-400 bg-white hover:bg-[#FFB7D5] transition flex items-center justify-center"
      >
        <FiArrowRight className="text-gray-700 text-2xl" />
      </button>
    </div>
  );
}

