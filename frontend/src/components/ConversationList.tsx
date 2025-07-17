import React from 'react';

interface ConversationSummary {
  conversation_id: string;
  last_message: string;
  updated_at: string;
}

interface ConversationListProps {
  conversations: ConversationSummary[];
  onSelect: (conversation_id: string) => void;
  selectedId?: string;
}

const ConversationList: React.FC<ConversationListProps> = ({ conversations, onSelect, selectedId }) => {
  return (
    <div className="w-full flex flex-col gap-1">
      {conversations.map(conv => (
        <button
          key={conv.conversation_id}
          className={`p-3 rounded text-left border hover:bg-muted transition-all ${selectedId === conv.conversation_id ? 'bg-primary/10 border-primary' : 'bg-background border-muted'}`}
          onClick={() => onSelect(conv.conversation_id)}
        >
          <div className="font-semibold truncate">{conv.last_message}</div>
          <div className="text-xs text-muted-foreground">{new Date(conv.updated_at).toLocaleString()}</div>
        </button>
      ))}
    </div>
  );
};

export default ConversationList;
