import { WebSocketEvent, ConnectionStatus } from '@/types';

class WebSocketService {
  private socket: WebSocket | null = null;
  private baseUrl: string;
  private apiKey: string;
  private listeners: Map<string, Set<(event: WebSocketEvent) => void>> = new Map();
  private statusListeners: Set<(status: ConnectionStatus) => void> = new Set();
  private currentStatus: ConnectionStatus = { status: 'disconnected' };
  private retryCount = 0;
  private maxRetries = 5;
  private retryDelay = 1000;

  constructor(baseUrl?: string, apiKey?: string) {
    this.baseUrl = baseUrl || import.meta.env.VITE_WS_BASE_URL || 'ws://localhost/ws';
    this.apiKey = apiKey || import.meta.env.VITE_API_KEY || '';
  }

  connect(conversationId: string): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      return;
    }

    this.updateStatus({ status: 'connecting' });

    const wsUrl = `${this.baseUrl}/${conversationId}`;
    this.socket = new WebSocket(wsUrl);

    // Add authorization header
    this.socket.onopen = () => {
      this.retryCount = 0;
      this.updateStatus({ 
        status: 'connected', 
        lastConnected: new Date().toISOString() 
      });
    };

    this.socket.onclose = () => {
      this.updateStatus({ status: 'disconnected' });
      this.scheduleReconnect();
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket connection error:', error);
      this.updateStatus({ status: 'error' });
      this.scheduleReconnect();
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const eventType = data.type || 'message';
        
        const wsEvent: WebSocketEvent = {
          type: eventType as any,
          data: data,
          timestamp: new Date().toISOString(),
        };

        this.notifyListeners(eventType, wsEvent);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
  }

  private scheduleReconnect(): void {
    if (this.retryCount >= this.maxRetries) {
      this.updateStatus({ status: 'error' });
      return;
    }

    this.retryCount++;
    const delay = this.retryDelay * Math.pow(2, this.retryCount - 1);

    setTimeout(() => {
      if (this.socket && this.socket.readyState !== WebSocket.OPEN) {
        this.connect(this.getCurrentConversationId());
      }
    }, delay);
  }

  private getCurrentConversationId(): string {
    // Extract conversation ID from current WebSocket URL
    const url = this.socket?.url || '';
    const match = url.match(/\/ws\/([^\/]+)/);
    return match ? match[1] : '';
  }

  private updateStatus(status: ConnectionStatus): void {
    this.currentStatus = { ...this.currentStatus, ...status };
    this.statusListeners.forEach(listener => listener(this.currentStatus));
  }

  private notifyListeners(eventType: string, event: WebSocketEvent): void {
    const listeners = this.listeners.get(eventType);
    if (listeners) {
      listeners.forEach(listener => listener(event));
    }

    // Also notify 'all' listeners
    const allListeners = this.listeners.get('all');
    if (allListeners) {
      allListeners.forEach(listener => listener(event));
    }
  }

  on(eventType: string, listener: (event: WebSocketEvent) => void): void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(listener);
  }

  off(eventType: string, listener: (event: WebSocketEvent) => void): void {
    const listeners = this.listeners.get(eventType);
    if (listeners) {
      listeners.delete(listener);
      if (listeners.size === 0) {
        this.listeners.delete(eventType);
      }
    }
  }

  onStatusChange(listener: (status: ConnectionStatus) => void): void {
    this.statusListeners.add(listener);
  }

  offStatusChange(listener: (status: ConnectionStatus) => void): void {
    this.statusListeners.delete(listener);
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    this.updateStatus({ status: 'disconnected' });
  }

  getStatus(): ConnectionStatus {
    return this.currentStatus;
  }

  send(eventName: string, data: any): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      const message = {
        type: eventName,
        data: data,
        timestamp: new Date().toISOString()
      };
      this.socket.send(JSON.stringify(message));
    }
  }
}

export default WebSocketService;