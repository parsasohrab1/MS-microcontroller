/**
 * WebSocket Service
 * سرویس WebSocket برای داده‌های real-time
 */

import { io, Socket } from 'socket.io-client';

class WebSocketService {
  private socket: Socket | null = null;
  private listeners: Map<string, Set<Function>> = new Map();
  
  connect(token: string) {
    if (this.socket?.connected) {
      return;
    }
    
    this.socket = io(process.env.REACT_APP_WS_URL || 'ws://localhost:8000', {
      auth: { token },
      transports: ['websocket']
    });
    
    this.socket.on('connect', () => {
      console.log('WebSocket connected');
    });
    
    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });
    
    // ثبت listeners موجود
    this.listeners.forEach((callbacks, event) => {
      callbacks.forEach(callback => {
        this.socket?.on(event, callback);
      });
    });
  }
  
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }
  
  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
    
    if (this.socket) {
      this.socket.on(event, callback);
    }
  }
  
  off(event: string, callback?: Function) {
    if (callback) {
      this.listeners.get(event)?.delete(callback);
      this.socket?.off(event, callback);
    } else {
      this.listeners.delete(event);
      this.socket?.off(event);
    }
  }
  
  emit(event: string, data: any) {
    this.socket?.emit(event, data);
  }
}

export const wsService = new WebSocketService();

export const useWebSocket = () => {
  return wsService;
};

