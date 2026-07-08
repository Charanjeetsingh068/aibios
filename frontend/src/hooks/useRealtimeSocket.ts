import { useEffect, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import { getAccessToken } from '../services/authService';

export type RealtimeHandlers = Partial<{
  'lead:new': (data: any) => void;
  'lead:updated': (data: any) => void;
  'lead:deleted': (data: any) => void;
  'deal:new': (data: any) => void;
  'deal:updated': (data: any) => void;
  'deal:deleted': (data: any) => void;
}>;

/** Connects to the backend's Socket.IO server (real-time, org-scoped) for the lifetime of the component. */
export function useRealtimeSocket(handlers: RealtimeHandlers) {
  const socketRef = useRef<Socket | null>(null);
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers;

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;

    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const socket = io(backendUrl, {
      path: '/socket.io',
      auth: { token },
      transports: ['websocket', 'polling'],
    });
    socketRef.current = socket;

    const eventNames: (keyof RealtimeHandlers)[] = [
      'lead:new', 'lead:updated', 'lead:deleted', 'deal:new', 'deal:updated', 'deal:deleted',
    ];
    eventNames.forEach((event) => {
      socket.on(event, (data: any) => handlersRef.current[event]?.(data));
    });

    return () => {
      socket.disconnect();
      socketRef.current = null;
    };
  }, []);

  return socketRef;
}
