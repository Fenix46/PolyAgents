import React, { useEffect, useRef } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
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
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Quando i messaggi cambiano, se eravamo in fondo, scorriamo automaticamente in fondo
  useEffect(() => {
    if (isAtBottomRef.current && scrollAreaRef.current) {
      const scrollElement = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollElement) {
        scrollElement.scrollTo({
          top: scrollElement.scrollHeight,
          behavior: 'smooth',
        });
      }
    }
  }, [messages, isAtBottomRef]);

  // Gestisce il cambio di stato "at bottom"
  const handleScroll = (event: React.UIEvent<HTMLDivElement>) => {
    const target = event.target as HTMLDivElement;
    const isAtBottom = target.scrollTop + target.clientHeight >= target.scrollHeight - 10;
    isAtBottomRef.current = isAtBottom;
  };

  return (
    <div className="flex-1 overflow-hidden">
      <ScrollArea 
        ref={scrollAreaRef}
        className="h-full w-full"
        onScroll={handleScroll}
      >
        <div className="space-y-2 p-4">
          {messages.length === 0 ? (
            <div className="h-full flex items-center justify-center text-muted-foreground">
              <p>Nessun messaggio. Inizia una conversazione!</p>
            </div>
          ) : (
            messages.map((message, index) => {
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
            })
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
