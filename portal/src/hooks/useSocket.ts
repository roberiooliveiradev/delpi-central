// src/hooks/useSocket.ts

import { useEffect, useRef } from "react";
import { io, Socket } from "socket.io-client";

interface UseSocketProps {
  token?: string;
  onNotification?: (data: any) => void;
}

export const useSocket = ({
  token,
  onNotification,
  onConnected,
}: UseSocketProps & { onConnected?: () => void }) => {
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    if (!token) return;

    socketRef.current = io("/", {
      path: "/socket.io",
      query: { token },
      transports: ["websocket"],
    });

    socketRef.current.on("connect", () => {
      console.log("✅ WebSocket conectado:", socketRef.current?.id);
      onConnected?.(); 
    });

    socketRef.current.on("notification", (data) => {
      console.log("📩 Notificação recebida:", data);
      onNotification?.(data);
    });

    socketRef.current.on("disconnect", () => {
      console.log("❌ WebSocket desconectado");
    });

    return () => {
      socketRef.current?.disconnect();
    };
  }, [token]);

  return socketRef;
};
