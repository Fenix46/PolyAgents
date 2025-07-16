import React, { useEffect, useRef } from 'react';
import { Virtuoso, VirtuosoHandle } from 'react-virtuoso';
import MessageBubble from './MessageBubble';
import { AgentBubble } from './MessageBubble';
import { Message, AgentResponse } from '@/types';
import { InteractiveFeedback } from '@/components/feedback/InteractiveFeedback';

interface VirtualizedChatListProps {
  messages: Message[];
  agentResponses: AgentResponse[];
  onSubmitFeedback: (messageId: string, feedback: any) => void;
  isAtBottomRef: React.MutableRefObject<boolean>;
  showMetadata?: boolean;
}

export function VirtualizedChatList({
  messages,
  agentResponses,
  onSubmitFeedback,
  isAtBottomRef,
  showMetadata = true
}: VirtualizedChatListProps) {
  const virtuosoRef = useRef<VirtuosoHandle>(null);

  // Quando i messaggi cambiano, se eravamo in fondo, scorriamo automaticamente in fondo
  useEffect(() => {
    if (isAtBottomRef.current && virtuosoRef.current) {
      virtuosoRef.current.scrollToIndex({
        index: messages.length - 1,
        behavior: 'smooth',
      });
    }
  }, [messages, isAtBottomRef]);

  // Funzione per renderizzare un messaggio
  const renderMessage = (index: number) => {
    const message = messages[index];
    
    // Trova le risposte degli agenti correlate a questo messaggio (se presenti)
    const relatedAgentResponses = agentResponses.filter(
      response => response.message_id === message.id
    );
    
    return (
      <div className="py-2" key={message.id}>
        <MessageBubble 
          message={message} 
          showMetadata={showMetadata}
        />
        
        {/* Mostra le risposte degli agenti se presenti */}
        {relatedAgentResponses.length > 0 && (
          <div className="mt-2 space-y-2">
            {relatedAgentResponses.map((agent, idx) => (
              <AgentBubble 
                key={agent.agent_id || `agent-${idx}`} 
                {...agent} 
                index={idx} 
              />
            ))}
          </div>
        )}
        
        {/* Feedback interattivo per i messaggi dell'utente */}
        {message.type === 'assistant' && (
          <InteractiveFeedback 
            messageId={message.id} 
            onSubmitFeedback={onSubmitFeedback} 
          />
        )}
      </div>
    );
  };

  return (
    <div className="flex-1 overflow-hidden">
      <Virtuoso
        ref={virtuosoRef}
        style={{ height: '100%', width: '100%' }}
        totalCount={messages.length}
        itemContent={renderMessage}
        overscan={200}
        increaseViewportBy={{ top: 300, bottom: 300 }}
        followOutput="auto"
        atBottomStateChange={(isAtBottom) => {
          isAtBottomRef.current = isAtBottom;
        }}
        components={{
          EmptyPlaceholder: () => (
            <div className="h-full flex items-center justify-center text-muted-foreground">
              <p>Nessun messaggio. Inizia una conversazione!</p>
            </div>
          ),
        }}
      />
    </div>
  );
}
