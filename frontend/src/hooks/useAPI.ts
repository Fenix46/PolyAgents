import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import APIService from '@/services/api';
import { APIConfig, ChatRequest, Conversation, SystemHealth, SystemStatistics } from '@/types';

const DEFAULT_CONFIG: APIConfig = {
  baseUrl: 'http://localhost:8000',
  apiKey: '',
  timeout: 30000,
  retryAttempts: 3,
};

export function useAPI() {
  const [config, setConfig] = useState<APIConfig>(DEFAULT_CONFIG);
  const [apiService] = useState(() => new APIService(config));

  useEffect(() => {
    apiService.updateConfig(config);
  }, [config, apiService]);

  const updateConfig = (newConfig: Partial<APIConfig>) => {
    setConfig(prev => ({ ...prev, ...newConfig }));
  };

  return {
    apiService,
    config,
    updateConfig,
  };
}

export function useChat() {
  const { apiService } = useAPI();
  const queryClient = useQueryClient();

  const chatMutation = useMutation({
    mutationFn: (request: ChatRequest) => apiService.chat(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });

  const startStreaming = async (conversationId: string) => {
    return apiService.startStreaming(conversationId);
  };

  return {
    sendMessage: chatMutation.mutate,
    isLoading: chatMutation.isPending,
    error: chatMutation.error,
    startStreaming,
  };
}

export function useConversations() {
  const { apiService } = useAPI();

  const {
    data: conversations,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => apiService.getRecentConversations(),
    staleTime: 30000,
  });

  const searchMutation = useMutation({
    mutationFn: (query: string) => apiService.searchConversations(query),
  });

  const getConversation = (id: string) => {
    return useQuery({
      queryKey: ['conversation', id],
      queryFn: () => apiService.getConversation(id),
      enabled: !!id,
    });
  };

  return {
    conversations,
    isLoading,
    error,
    refetch,
    searchConversations: searchMutation.mutate,
    searchResults: searchMutation.data,
    isSearching: searchMutation.isPending,
    getConversation,
  };
}

export function useSystemHealth() {
  const { apiService } = useAPI();

  return useQuery({
    queryKey: ['system-health'],
    queryFn: () => apiService.getSystemHealth(),
    refetchInterval: 30000,
  });
}

export function useSystemStatistics() {
  const { apiService } = useAPI();

  return useQuery({
    queryKey: ['system-statistics'],
    queryFn: () => apiService.getSystemStatistics(),
    refetchInterval: 60000,
  });
}