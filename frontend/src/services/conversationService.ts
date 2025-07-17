import axios from 'axios';

export interface ConversationSummary {
  conversation_id: string;
  last_message: string;
  updated_at: string;
}

export interface ConversationDetail {
  conversation_id: string;
  messages: Array<{
    id: string;
    sender: string;
    content: string;
    agent?: string;
    fusion?: boolean;
    timestamp?: string;
  }>;
}

export const getRecentConversations = async (limit = 10) => {
  const res = await axios.get<{ conversations: ConversationSummary[] }>(`/conversations/recent?limit=${limit}`);
  return res.data.conversations;
};

export const getConversationDetail = async (conversation_id: string) => {
  const res = await axios.get<ConversationDetail>(`/conversations/${conversation_id}`);
  return res.data;
};

export const searchConversations = async (query: string, limit = 10) => {
  const res = await axios.post<{ results: ConversationSummary[] }>(`/conversations/search`, { query, limit });
  return res.data.results;
};
