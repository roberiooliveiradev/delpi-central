// src/hooks/useSocket.ts

import { useEffect, useRef } from "react";
import { io, Socket } from "socket.io-client";

interface UseSocketProps {
  token?: string;
  onNotification?: (data: any) => void;
  onAdminChanged?: (data: any) => void;
  onConnected?: () => void;
}

export const useSocket = ({
  token,
  onNotification,
  onAdminChanged,
  onConnected,
}: UseSocketProps) => {
  const socketRef = useRef<Socket | null>(null);

  // 🔒 callbacks estáveis via ref (evita recriar socket)
  const onNotificationRef = useRef(onNotification);
  const onAdminChangedRef = useRef(onAdminChanged);
  const onConnectedRef = useRef(onConnected);

  // sempre atualiza refs quando callbacks mudam
  useEffect(() => {
    onNotificationRef.current = onNotification;
  }, [onNotification]);

  useEffect(() => {
    onAdminChangedRef.current = onAdminChanged;
  }, [onAdminChanged]);

  useEffect(() => {
    onConnectedRef.current = onConnected;
  }, [onConnected]);

  // 🔥 socket depende APENAS do token
  useEffect(() => {
    if (!token) return;

    const socket = io("/", {
      path: "/socket.io", // ajuste se necessário
      query: { token },
      transports: ["websocket"],
    });

    socketRef.current = socket;

    socket.on("connect", () => {
      console.log("✅ WebSocket conectado:", socket.id);
      onConnectedRef.current?.();
    });

    socket.on("notification", (data) => {
      onNotificationRef.current?.(data);
    });

    socket.on("admin.changed", (data) => {
      console.log("📡 admin.changed recebido:", data);
      onAdminChangedRef.current?.(data);
    });

    socket.on("disconnect", () => {
      console.log("❌ WebSocket desconectado");
    });

    return () => {
      socket.disconnect();
    };
  }, [token]); // 🔥 SOMENTE token

  return socketRef;
};