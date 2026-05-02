import { useEffect, useState, useRef } from 'react';

interface NotificationMessage {
  type: 'notification' | 'ticket_count';
  message?: string;
  n_type?: string;
  count?: number;
}

export const useNotifications = () => {
  const [ticketCount, setTicketCount] = useState<number>(0);
  const [latestNotification, setLatestNotification] = useState<any>(null);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const socketUrl = `${protocol}//${host}/ws/notifications/?token=${token}`;

    const connect = () => {
      const ws = new WebSocket(socketUrl);

      ws.onopen = () => {
        console.log('WebSocket Connected');
      };

      ws.onmessage = (event) => {
        const data: NotificationMessage = JSON.parse(event.data);
        
        if (data.type === 'notification') {
          setLatestNotification(data);
          // Trigger browser notification if possible
          if (Notification.permission === 'granted') {
            new Notification('Experiment Update', { body: data.message });
          }
        } else if (data.type === 'ticket_count') {
          setTicketCount(data.count ?? 0);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket Disconnected. Retrying in 5s...');
        setTimeout(connect, 5000);
      };

      socketRef.current = ws;
    };

    connect();

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, []);

  return { ticketCount, latestNotification };
};
