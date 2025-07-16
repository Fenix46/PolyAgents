import { useState, useEffect, useCallback } from 'react';
import { Message, AgentResponse, Conversation } from '@/types';
import { useConversationCache } from './useConversationCache';

interface UseLazyConversationProps {
  conversationId: string;
  initialMessages?: Message[];
  initialAgentResponses?: AgentResponse[];
  pageSize?: number;
  fetchMessages: (conversationId: string, offset: number, limit: number) => Promise<{
    messages: Message[];
    agentResponses: AgentResponse[];
    hasMore: boolean;
  }>;
}

export function useLazyConversation({
  conversationId,
  initialMessages = [],
  initialAgentResponses = [],
  pageSize = 20,
  fetchMessages
}: UseLazyConversationProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [agentResponses, setAgentResponses] = useState<AgentResponse[]>(initialAgentResponses);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(initialMessages.length >= pageSize);
  const [offset, setOffset] = useState(initialMessages.length);
  const { cacheConversation, getCachedConversation } = useConversationCache();

  // Carica i messaggi iniziali dalla cache se disponibili
  useEffect(() => {
    if (initialMessages.length === 0 && conversationId) {
      const cached = getCachedConversation(conversationId);
      if (cached) {
        setMessages(cached.messages);
        setAgentResponses(cached.agentResponses);
        setOffset(cached.messages.length);
        setHasMore(cached.messages.length >= pageSize);
      }
    }
  }, [conversationId, initialMessages.length, getCachedConversation, pageSize]);

  // Aggiorna la cache quando i messaggi cambiano
  useEffect(() => {
    if (conversationId && messages.length > 0) {
      cacheConversation(conversationId, messages, agentResponses);
    }
  }, [conversationId, messages, agentResponses, cacheConversation]);

  // Funzione per caricare più messaggi
  const loadMoreMessages = useCallback(async () => {
    if (loading || !hasMore || !conversationId) return;
    
    setLoading(true);
    try {
      const result = await fetchMessages(conversationId, offset, pageSize);
      
      // Aggiungi i nuovi messaggi all'inizio dell'array (messaggi più vecchi)
      setMessages(prevMessages => [
        ...result.messages.filter(msg => 
          !prevMessages.some(existing => existing.id === msg.id)
        ),
        ...prevMessages
      ]);
      
      // Aggiungi le nuove risposte degli agenti
      setAgentResponses(prevResponses => [
        ...result.agentResponses.filter(resp => 
          !prevResponses.some(existing => existing.id === resp.id)
        ),
        ...prevResponses
      ]);
      
      setOffset(prev => prev + result.messages.length);
      setHasMore(result.hasMore);
    } catch (error) {
      console.error('Errore nel caricamento dei messaggi:', error);
    } finally {
      setLoading(false);
    }
  }, [conversationId, fetchMessages, hasMore, loading, offset, pageSize]);

  // Funzione per aggiungere un nuovo messaggio (ad es. quando l'utente invia un messaggio)
  const addMessage = useCallback((message: Message, newAgentResponses: AgentResponse[] = []) => {
    setMessages(prev => [...prev, message]);
    
    if (newAgentResponses.length > 0) {
      setAgentResponses(prev => [...prev, ...newAgentResponses]);
    }
  }, []);

  return {
    messages,
    agentResponses,
    loading,
    hasMore,
    loadMoreMessages,
    addMessage
  };
}
