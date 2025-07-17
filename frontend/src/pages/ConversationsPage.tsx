import React, { useEffect, useState } from 'react';
import ConversationList from '../components/ConversationList';
import ChatHistory from '../components/ChatHistory';
import { getRecentConversations, getConversationDetail, ConversationSummary, ConversationDetail } from '../services/conversationService';

const ConversationsPage: React.FC = () => {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | undefined>();
  const [detail, setDetail] = useState<ConversationDetail | null>(null);

  useEffect(() => {
    getRecentConversations().then(setConversations);
  }, []);

  useEffect(() => {
    if (selectedId) {
      getConversationDetail(selectedId).then(setDetail);
    }
  }, [selectedId]);

  return (
    <div className="flex h-full w-full">
      <div className="w-72 border-r p-2 bg-background">
        <h2 className="font-bold mb-2">Conversazioni Recenti</h2>
        <ConversationList conversations={conversations} onSelect={setSelectedId} selectedId={selectedId} />
      </div>
      <div className="flex-1 p-4 overflow-y-auto">
        {detail ? (
          <>
            <h3 className="font-semibold mb-2">Dettaglio Conversazione</h3>
            <ChatHistory messages={detail.messages} />
          </>
        ) : (
          <div className="text-muted-foreground mt-10 text-center">Seleziona una conversazione per vedere i dettagli</div>
        )}
      </div>
    </div>
  );
};

export default ConversationsPage;
