import { useState, useEffect, useCallback, useRef } from 'react';
import WebSocketService from '@/services/websocket';
import { WebSocketEvent, ConnectionStatus } from '@/types';

export function useWebSocket(conversationId: string, apiKey: string) {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    status: 'disconnected',
  });
  const [events, setEvents] = useState<WebSocketEvent[]>([]);
  const wsService = useRef<WebSocketService | null>(null);

  useEffect(() => {
    if (!conversationId || !apiKey) return;

    wsService.current = new WebSocketService('http://localhost:8000', apiKey);

    const handleStatusChange = (status: ConnectionStatus) => {
      setConnectionStatus(status);
    };

    const handleEvent = (event: WebSocketEvent) => {
      setEvents(prev => [...prev, event]);
    };

    wsService.current.onStatusChange(handleStatusChange);
    wsService.current.on('all', handleEvent);
    wsService.current.connect(conversationId);

    return () => {
      wsService.current?.disconnect();
      wsService.current = null;
    };
  }, [conversationId, apiKey]);

  const emit = useCallback((eventName: string, data: any) => {
    wsService.current?.emit(eventName, data);
  }, []);

  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  return {
    connectionStatus,
    events,
    emit,
    clearEvents,
  };
}

export function useAgentStatus(conversationId: string, apiKey: string) {
  const [agentStatuses, setAgentStatuses] = useState<Map<string, string>>(new Map());
  const [typingAgents, setTypingAgents] = useState<Set<string>>(new Set());
  const { events } = useWebSocket(conversationId, apiKey);

  useEffect(() => {
    events.forEach(event => {
      switch (event.type) {
        case 'agent_status':
          setAgentStatuses(prev => new Map(prev).set(event.data.agent_id, event.data.status));
          break;
        case 'agent_typing':
          setTypingAgents(prev => new Set(prev).add(event.data.agent_id));
          break;
        case 'agent_stopped_typing':
          setTypingAgents(prev => {
            const newSet = new Set(prev);
            newSet.delete(event.data.agent_id);
            return newSet;
          });
          break;
      }
    });
  }, [events]);

  return {
    agentStatuses,
    typingAgents,
  };
}