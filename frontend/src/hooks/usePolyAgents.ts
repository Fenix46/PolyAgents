import { useState, useEffect, useCallback } from 'react';
import APIService from '@/services/api';
import WebSocketService from '@/services/websocket';
import { 
  ChatRequest, 
  ChatResponse, 
  Conversation, 
  Message, 
  WebSocketEvent, 
  ConnectionStatus,
  SystemHealth,
  SystemStatistics 
} from '@/types';

export const usePolyAgents = () => {
  const [apiService] = useState(() => new APIService());
  const [wsService] = useState(() => new WebSocketService());
  
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({ status: 'disconnected' });
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [systemStats, setSystemStats] = useState<SystemStatistics | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // WebSocket event handlers
  useEffect(() => {
    const handleWebSocketEvent = (event: WebSocketEvent) => {
      switch (event.type) {
        case 'message':
          if (event.data.message) {
            setMessages(prev => [...prev, event.data.message]);
          }
          break;
        case 'agent_status':
          // Update agent status in current conversation
          if (currentConversation) {
            setCurrentConversation(prev => prev ? {
              ...prev,
              agents: prev.agents.map(agent => 
                agent.id === event.data.agent_id 
                  ? { ...agent, status: event.data.status }
                  : agent
              )
            } : null);
          }
          break;
        case 'consensus_update':
          // Handle consensus updates
          console.log('Consensus update:', event.data);
          break;
        case 'system_update':
          // Handle system updates
          console.log('System update:', event.data);
          break;
        case 'error':
          setError(event.data.message || 'WebSocket error occurred');
          break;
      }
    };

    const handleStatusChange = (status: ConnectionStatus) => {
      setConnectionStatus(status);
    };

    wsService.on('all', handleWebSocketEvent);
    wsService.onStatusChange(handleStatusChange);

    return () => {
      wsService.off('all', handleWebSocketEvent);
      wsService.offStatusChange(handleStatusChange);
    };
  }, [wsService, currentConversation]);

  // Load recent conversations
  const loadConversations = useCallback(async () => {
    try {
      setIsLoading(true);
      const recentConversations = await apiService.getRecentConversations();
      setConversations(recentConversations);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load conversations');
    } finally {
      setIsLoading(false);
    }
  }, [apiService]);

  // Load conversation details
  const loadConversation = useCallback(async (conversationId: string) => {
    try {
      setIsLoading(true);
      const conversation = await apiService.getConversation(conversationId);
      setCurrentConversation(conversation);
      
      // Connect to WebSocket for this conversation
      wsService.connect(conversationId);
      
      // Load messages (you might need to implement this endpoint)
      // const conversationMessages = await apiService.getConversationMessages(conversationId);
      // setMessages(conversationMessages);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load conversation');
    } finally {
      setIsLoading(false);
    }
  }, [apiService, wsService]);

  // Send message
  const sendMessage = useCallback(async (request: ChatRequest) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await apiService.chat(request);
      
      // Add user message to the list
      const userMessage: Message = {
        id: `user-${Date.now()}`,
        conversation_id: response.conversation_id,
        type: 'user',
        content: request.message,
        timestamp: new Date().toISOString(),
      };
      
      // Add agent response to the list
      const agentMessage: Message = {
        id: response.message_id,
        conversation_id: response.conversation_id,
        type: 'consensus',
        content: response.response,
        timestamp: new Date().toISOString(),
        metadata: response.metadata,
      };
      
      setMessages(prev => [...prev, userMessage, agentMessage]);
      
      return response;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [apiService]);

  // Load system health
  const loadSystemHealth = useCallback(async () => {
    try {
      const health = await apiService.getSystemHealth();
      setSystemHealth(health);
    } catch (err) {
      console.error('Failed to load system health:', err);
    }
  }, [apiService]);

  // Load system statistics
  const loadSystemStats = useCallback(async () => {
    try {
      const stats = await apiService.getSystemStatistics();
      setSystemStats(stats);
    } catch (err) {
      console.error('Failed to load system statistics:', err);
    }
  }, [apiService]);

  // Search conversations
  const searchConversations = useCallback(async (query: string) => {
    try {
      setIsLoading(true);
      const results = await apiService.searchConversations(query);
      setConversations(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to search conversations');
    } finally {
      setIsLoading(false);
    }
  }, [apiService]);

  // Disconnect WebSocket
  const disconnect = useCallback(() => {
    wsService.disconnect();
  }, [wsService]);

  // Initialize
  useEffect(() => {
    loadConversations();
    loadSystemHealth();
    loadSystemStats();
  }, [loadConversations, loadSystemHealth, loadSystemStats]);

  return {
    // State
    conversations,
    currentConversation,
    messages,
    connectionStatus,
    systemHealth,
    systemStats,
    isLoading,
    error,
    
    // Actions
    loadConversations,
    loadConversation,
    sendMessage,
    searchConversations,
    disconnect,
    loadSystemHealth,
    loadSystemStats,
    
    // Services
    apiService,
    wsService,
  };
}; 