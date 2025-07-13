import { APIConfig, ChatRequest, ChatResponse, Conversation, SystemHealth, SystemStatistics } from '@/types';

class APIService {
  private config: APIConfig;

  constructor(config?: Partial<APIConfig>) {
    this.config = {
      baseUrl: config?.baseUrl || import.meta.env.VITE_API_BASE_URL || '/api',
      apiKey: config?.apiKey || import.meta.env.VITE_API_KEY || '',
      timeout: config?.timeout || 120000, // Aumentato a 2 minuti per risposte più lunghe
      retryAttempts: config?.retryAttempts || 3,
    };
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.config.baseUrl}${endpoint}`;
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    
    // Only add Authorization header if API key is provided
    if (this.config.apiKey && this.config.apiKey.trim() !== '') {
      headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }
    
    const response = await fetch(url, {
      ...options,
      headers,
      signal: AbortSignal.timeout(this.config.timeout),
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async chat(request: ChatRequest): Promise<ChatResponse> {
    return this.makeRequest<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async startStreaming(conversationId: string, request: ChatRequest): Promise<Response> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    
    // Only add Authorization header if API key is provided
    if (this.config.apiKey && this.config.apiKey.trim() !== '') {
      headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }
    
    return fetch(`${this.config.baseUrl}/stream/${conversationId}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });
  }

  async getRecentConversations(): Promise<Conversation[]> {
    const response = await this.makeRequest<{ conversations: Conversation[] }>('/conversations/recent');
    return response.conversations || [];
  }

  async getConversation(id: string): Promise<Conversation> {
    return this.makeRequest<Conversation>(`/conversations/${id}`);
  }

  async searchConversations(query: string): Promise<Conversation[]> {
    const response = await this.makeRequest<{ results: Conversation[] }>('/conversations/search', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
    return response.results || [];
  }

  async getSystemHealth(): Promise<SystemHealth> {
    return this.makeRequest<SystemHealth>('/health/detailed');
  }

  async getSystemStatistics(): Promise<SystemStatistics> {
    return this.makeRequest<SystemStatistics>('/statistics');
  }

  updateConfig(config: Partial<APIConfig>) {
    this.config = { ...this.config, ...config };
  }
}

export default APIService;