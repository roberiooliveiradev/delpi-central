// src/hooks/useSocket.ts

import { useEffect, useRef } from "react";
import { io, Socket } from "socket.io-client";

import {
  APP_USAGE_OPEN_EVENT,
  type AppUsageOpenDetail,
} from "../utils/appUsageEvents";

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
  const activeAppRef = useRef<{ appId: string; routePath: string } | null>(null);

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

  // ============================================
  // SOCKET INIT (apenas uma vez)
  // ============================================

  useEffect(() => {
    if (socketRef.current) return;

    console.log("🔌 Inicializando WebSocket...");

    const socket = io("/", {
      path: "/socket.io",
      transports: ["websocket"],
      reconnection: true,
      autoConnect: false,
    });

    socketRef.current = socket;

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

    return () => {
      console.log("🧹 WebSocket finalizado");

      socket.removeAllListeners();
      socket.disconnect();
      socketRef.current = null;
    };
  }, []);

  // ============================================
  // AUTH UPDATE (quando token muda)
  // ============================================

  useEffect(() => {
    const socket = socketRef.current;

    if (!socket) return;
    if (!token || token.length < 20) return;

    console.log("🔑 Atualizando token WebSocket");

    socket.auth = { token };

    if (!socket.connected) {
      socket.connect();
    } else {
      // reautentica sem recriar conexão
      socket.emit("auth.refresh", { token });
    }
  }, [token]);

  useEffect(() => {
    const socket = socketRef.current;
    if (!socket || !token || token.length < 20) return;

    const emitUsagePing = () => {
      if (!socket.connected) return;

      socket.emit("presence.ping");

      const activeApp = activeAppRef.current;
      if (activeApp?.appId) {
        socket.emit("app_usage.ping", {
          appId: activeApp.appId,
          routePath: activeApp.routePath,
        });
      }
    };

    const onConnect = () => {
      const activeApp = activeAppRef.current;
      if (activeApp?.appId) {
        socket.emit("app_usage.open", {
          appId: activeApp.appId,
          routePath: activeApp.routePath,
        });
      }

      emitUsagePing();
    };

    socket.on("connect", onConnect);

    const intervalId = window.setInterval(emitUsagePing, 45_000);

    return () => {
      socket.off("connect", onConnect);
      window.clearInterval(intervalId);
    };
  }, [token]);

  useEffect(() => {
    const onAppOpened = (event: Event) => {
      const custom = event as CustomEvent<AppUsageOpenDetail>;
      const appId = custom.detail?.appId;
      const routePath = custom.detail?.routePath;

      if (!appId) return;

      activeAppRef.current = { appId, routePath: routePath || "/" };

      const socket = socketRef.current;
      if (socket?.connected) {
        socket.emit("app_usage.open", {
          appId,
          routePath: routePath || "/",
        });
      }
    };

    window.addEventListener(APP_USAGE_OPEN_EVENT, onAppOpened);

    return () => {
      window.removeEventListener(APP_USAGE_OPEN_EVENT, onAppOpened);
    };
  }, []);

  return socketRef;
};