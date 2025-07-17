import React from 'react';

interface Message {
  id: string;
  sender: string;
  content: string;
  agent?: string;
  fusion?: boolean;
  timestamp?: string;
}

interface ChatHistoryProps {
  messages: Message[];
}

const ChatHistory: React.FC<ChatHistoryProps> = ({ messages }) => {
  return (
    <div className="flex flex-col gap-2 mb-4 overflow-y-auto max-h-[60vh] px-2">
      {messages.map(msg => (
        <div
          key={msg.id}
          className={`p-2 rounded-lg ${msg.fusion ? 'bg-primary/10 border-primary border-2' : 'bg-card border border-muted'} shadow-sm`}
        >
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm text-primary">{msg.sender}</span>
            {msg.agent && <span className="text-xs bg-secondary px-2 py-0.5 rounded">{msg.agent}</span>}
            {msg.fusion && <span className="text-xs bg-primary text-white px-2 py-0.5 rounded">Fusione</span>}
            <span className="text-xs text-muted-foreground ml-auto">{msg.timestamp}</span>
          </div>
          <div className="mt-1 whitespace-pre-line">{msg.content}</div>
        </div>
      ))}
    </div>
  );
};

export default ChatHistory;
