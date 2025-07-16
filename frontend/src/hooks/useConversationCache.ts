import { useState, useEffect } from 'react';
import { Message, Conversation, AgentResponse } from '@/types';

// Definizione della struttura della cache
interface CacheItem {
  messages: Message[];
  agentResponses: AgentResponse[];
  timestamp: number;
  expiresAt: number;
}

interface ConversationCache {
  [conversationId: string]: CacheItem;
}

// Configurazione della cache
const CACHE_EXPIRY_TIME = 30 * 60 * 1000; // 30 minuti in millisecondi
const CACHE_KEY = 'polyagent-conversation-cache';

export function useConversationCache() {
  const [cache, setCache] = useState<ConversationCache>(() => {
    // Carica la cache dal localStorage all'avvio
    try {
      const storedCache = localStorage.getItem(CACHE_KEY);
      if (storedCache) {
        const parsedCache = JSON.parse(storedCache);
        // Pulisci le voci scadute
        const now = Date.now();
        const cleanedCache = Object.entries(parsedCache).reduce((acc, [key, value]) => {
          const item = value as CacheItem;
          if (item.expiresAt > now) {
            acc[key] = item;
          }
          return acc;
        }, {} as ConversationCache);
        
        return cleanedCache;
      }
    } catch (error) {
      console.error('Errore nel caricamento della cache:', error);
    }
    return {};
  });

  // Salva la cache nel localStorage quando cambia
  useEffect(() => {
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify(cache));
    } catch (error) {
      console.error('Errore nel salvataggio della cache:', error);
    }
  }, [cache]);

  // Funzione per aggiungere/aggiornare una conversazione nella cache
  const cacheConversation = (
    conversationId: string, 
    messages: Message[], 
    agentResponses: AgentResponse[]
  ) => {
    const now = Date.now();
    setCache(prev => ({
      ...prev,
      [conversationId]: {
        messages,
        agentResponses,
        timestamp: now,
        expiresAt: now + CACHE_EXPIRY_TIME
      }
    }));
  };

  // Funzione per ottenere una conversazione dalla cache
  const getCachedConversation = (conversationId: string) => {
    const cachedItem = cache[conversationId];
    if (cachedItem && cachedItem.expiresAt > Date.now()) {
      return {
        messages: cachedItem.messages,
        agentResponses: cachedItem.agentResponses
      };
    }
    return null;
  };

  // Funzione per invalidare una specifica conversazione nella cache
  const invalidateCache = (conversationId: string) => {
    setCache(prev => {
      const newCache = { ...prev };
      delete newCache[conversationId];
      return newCache;
    });
  };

  // Funzione per pulire le voci scadute nella cache
  const cleanExpiredCache = () => {
    const now = Date.now();
    setCache(prev => {
      const newCache = { ...prev };
      Object.keys(newCache).forEach(key => {
        if (newCache[key].expiresAt <= now) {
          delete newCache[key];
        }
      });
      return newCache;
    });
  };

  // Pulisci periodicamente la cache (ogni 5 minuti)
  useEffect(() => {
    const interval = setInterval(cleanExpiredCache, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  return {
    cacheConversation,
    getCachedConversation,
    invalidateCache,
    cleanExpiredCache
  };
}
