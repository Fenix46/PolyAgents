import React, { useState } from 'react';

interface PromptInputProps {
  onSend: (prompt: string) => void;
  loading: boolean;
}

const PromptInput: React.FC<PromptInputProps> = ({ onSend, loading }) => {
  const [prompt, setPrompt] = useState('');

  const handleSend = () => {
    if (prompt.trim()) {
      onSend(prompt);
      setPrompt('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !loading) {
      handleSend();
    }
  };

  return (
    <div className="flex gap-2 items-center w-full p-2 border-t bg-background">
      <input
        className="flex-1 p-2 rounded border bg-[#181a20] text-white placeholder:text-gray-400 focus:border-primary focus:ring-2 focus:ring-primary focus:outline-none transition-all"
        type="text"
        placeholder="Scrivi il tuo prompt..."
        value={prompt}
        disabled={loading}
        onChange={e => setPrompt(e.target.value)}
        onKeyDown={handleKeyDown}
      />
      <button
        className="px-4 py-2 rounded bg-primary text-white disabled:opacity-50"
        onClick={handleSend}
        disabled={loading || !prompt.trim()}
      >
        Invia
      </button>
    </div>
  );
};

export default PromptInput;
