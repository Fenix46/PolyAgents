import axios from 'axios';

export interface ChatRequest {
  message: string;
  agents?: {
    count?: number;
    turns?: number;
  };
  conversation_id?: string;
}

export interface ChatResponse {
  conversation_id: string;
  message_id: string;
  response: string;
  agent_responses?: Record<string, string>;
  consensus?: string;
  metadata?: any;
}

export interface StreamResponse {
  conversation_id: string;
  status: string;
  websocket_url: string;
}

// Creo un'istanza Axios configurata con il base URL
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  // Nessun timeout per le richieste al backend multi-agente
  // che richiede tempo per elaborare le risposte
  timeout: 0,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Log della configurazione per debugging
console.log('[API Config]', {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  apiKey: import.meta.env.VITE_API_KEY ? 'Configurata' : 'Non configurata'
});

// Se c'è una API key configurata, aggiungo l'header di autorizzazione
if (import.meta.env.VITE_API_KEY) {
  api.defaults.headers.common['Authorization'] = `Bearer ${import.meta.env.VITE_API_KEY}`;
}

// Aggiungo interceptors per gestire errori e logging
api.interceptors.request.use(
  config => {
    console.log(`[API] Richiesta a: ${config.baseURL}${config.url}`);
    return config;
  },
  error => {
    console.error('[API] Errore nella richiesta:', error);
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  response => response,
  error => {
    console.error('[API] Errore nella risposta:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Metodo sincrono - attende la risposta completa (può richiedere molto tempo)
export const sendChat = async (data: ChatRequest) => {
  console.log('[API] Invio richiesta sincrona a /chat');
  const res = await api.post<ChatResponse>('/chat', data);
  return res.data;
};

// Metodo asincrono - avvia lo streaming e restituisce subito l'ID conversazione
export const startStreamingChat = async (data: ChatRequest): Promise<StreamResponse> => {
  console.log('[API] Avvio streaming chat');
  // Genera un ID conversazione se non fornito
  const conversation_id = data.conversation_id || `conv-${Date.now()}`;
  const res = await api.post<StreamResponse>(`/stream/${conversation_id}`, data);
  return res.data;
};

// Metodo per verificare lo stato di una conversazione in corso
export const getConversationStatus = async (conversation_id: string) => {
  console.log(`[API] Verifica stato conversazione ${conversation_id}`);
  const res = await api.get(`/conversations/${conversation_id}`);
  return res.data;
};
