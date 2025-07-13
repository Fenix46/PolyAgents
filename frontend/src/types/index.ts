export interface Agent {
  id: string;
  name: string;
  model: string;
  temperature: number;
  status: 'idle' | 'thinking' | 'responding' | 'offline';
  color: string;
  responseTime?: number;
  turns?: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  type: 'user' | 'agent' | 'system' | 'consensus';
  content: string;
  agent_id?: string;
  timestamp: string;
  metadata?: {
    response_time?: number;
    model?: string;
    temperature?: number;
  };
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  agents: Agent[];
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  agents?: {
    count: number;
    turns: number;
    temperature: number;
    model: string;
  };
}

export interface AgentResponse {
  agent_id: string;
  content: string;
  status?: 'thinking' | 'ready' | 'error';
  error?: string;
}

export interface ChatResponse {
  conversation_id: string;
  message_id: string;
  agent_responses: AgentResponse[];
  consensus: {
    content: string;
    explanation?: string;
  };
  metadata?: any;
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  api_version: string;
  uptime: number;
  active_connections: number;
  memory_usage: number;
  cpu_usage: number;
}

export interface SystemStatistics {
  total_conversations: number;
  total_messages: number;
  active_agents: number;
  avg_response_time: number;
  uptime: number;
}

export interface WebSocketEvent {
  type: 'message' | 'agent_status' | 'consensus_update' | 'system_update' | 'error' | 'agent_typing' | 'agent_stopped_typing';
  data: any;
  timestamp: string;
}

export interface ConnectionStatus {
  status: 'connected' | 'connecting' | 'disconnected' | 'error';
  lastConnected?: string;
  retryCount?: number;
}

export interface VotingProgress {
  agent_id: string;
  vote: 'agree' | 'disagree' | 'abstain';
  confidence: number;
}

export interface ConsensusState {
  status: 'pending' | 'in_progress' | 'reached' | 'failed';
  votes: VotingProgress[];
  final_decision?: string;
  confidence_score?: number;
}

export interface UISettings {
  theme: 'dark' | 'light' | 'auto';
  autoScroll: boolean;
  soundEnabled: boolean;
  messageGrouping: boolean;
  sidebarCollapsed: boolean;
  rightPanelVisible: boolean;
}

export interface APIConfig {
  baseUrl: string;
  apiKey: string;
  timeout: number;
  retryAttempts: number;
}