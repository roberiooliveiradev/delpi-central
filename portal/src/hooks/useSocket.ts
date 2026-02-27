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

  // 🔒 refs estáveis (evita recriação do socket)
  const onNotificationRef = useRef(onNotification);
  const onAdminChangedRef = useRef(onAdminChanged);
  const onConnectedRef = useRef(onConnected);

  useEffect(() => {
    onNotificationRef.current = onNotification;
  }, [onNotification]);

  useEffect(() => {
    onAdminChangedRef.current = onAdminChanged;
  }, [onAdminChanged]);

  useEffect(() => {
    onConnectedRef.current = onConnected;
  }, [onConnected]);

  useEffect(() => {
    // 🔥 Só conecta se token válido
    if (!token || token.length < 20) {
      return;
    }

    // 🔥 Garante apenas UMA conexão ativa
    if (socketRef.current) {
      socketRef.current.removeAllListeners();
      socketRef.current.disconnect();
      socketRef.current = null;
    }

    console.log("🔌 Iniciando WebSocket...");

    const socket = io("/", {
      path: "/socket.io",
      query: { token },
      transports: ["websocket"],
      reconnection: true,
    });

    socketRef.current = socket;

    // =========================
    // EVENT HANDLERS
    // =========================

    const handleConnect = () => {
      console.log("✅ WebSocket conectado:", socket.id);
      onConnectedRef.current?.();
    };

    const handleNotification = (data: any) => {
      onNotificationRef.current?.(data);
    };

    const handleAdminChanged = (data: any) => {
      console.log("🚀 admin.changed:", data);
      onAdminChangedRef.current?.(data);
    };

    const handleDisconnect = (reason: string) => {
      console.log("❌ WebSocket desconectado:", reason);
    };

    const handleError = (err: any) => {
      console.error("🔥 WebSocket erro:", err);
    };

    socket.on("connect", handleConnect);
    socket.on("notification", handleNotification);
    socket.on("admin.changed", handleAdminChanged);
    socket.on("disconnect", handleDisconnect);
    socket.on("connect_error", handleError);

    // =========================
    // CLEANUP
    // =========================

    return () => {
      if (!socketRef.current) return;

      socketRef.current.off("connect", handleConnect);
      socketRef.current.off("notification", handleNotification);
      socketRef.current.off("admin.changed", handleAdminChanged);
      socketRef.current.off("disconnect", handleDisconnect);
      socketRef.current.off("connect_error", handleError);

      socketRef.current.disconnect();
      socketRef.current = null;

      console.log("🧹 WebSocket finalizado");
    };
  }, [token]);

  return socketRef;
};