import { useState, useEffect, useRef } from "react";
import { FiArrowRight } from "react-icons/fi";  // Install: npm install react-icons

interface ChatBoxProps {
  onSend: (message: string) => void;
  onTyping?: () => void;  // Callback for when user starts typing
}

export default function ChatBox({ onSend, onTyping }: ChatBoxProps) {
  const [input, setInput] = useState("");
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const DEBOUNCE_DELAY = 400; // 400ms debounce

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setInput(value);
    
    // Clear existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    
    // Notify parent that user is typing (for immediate feedback)
    if (onTyping && value.trim().length > 0) {
      onTyping();
    }
    
    // Set new debounce timer (for auto-suggestions, etc.)
    debounceTimerRef.current = setTimeout(() => {
      // Debounced action could go here (e.g., auto-suggestions)
    }, DEBOUNCE_DELAY);
  };

  const handleSend = () => {
    if (!input.trim()) return;
    
    // Clear debounce timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = null;
    }
    
    onSend(input);
    setInput("");
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  return (
    <div className="flex items-center w-full bg-[#F3F7FF] border border-gray-300 rounded-full px-6 py-3">
      <input
        type="text"
        className="flex-1 bg-transparent text-[#4D4D4D] placeholder:text-gray-400 focus:outline-none text-base"
        placeholder="Hi, I am pharmamiku, how can I help you today?"
        value={input}
        onChange={handleInputChange}
        onKeyDown={handleKeyPress}
      />
      <button
        onClick={handleSend}
        className="ml-2 p-2 rounded-full hover:bg-[#FFB7D5] transition flex items-center justify-center"
        disabled={!input.trim()}
      >
        <FiArrowRight className="text-gray-600 text-xl" />
      </button>
    </div>
  );
}

