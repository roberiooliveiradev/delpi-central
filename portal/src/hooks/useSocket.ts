// src/hooks/useSocket.ts

import { useEffect, useRef } from "react";
import { io, Socket } from "socket.io-client";

import {
  APP_USAGE_CLOSE_EVENT,
  APP_USAGE_OPEN_EVENT,
  type AppUsageCloseDetail,
  type AppUsageOpenDetail,
} from "../utils/appUsageEvents";
import {
  type ActiveAppUsage,
  shouldCloseExternalUsage,
  shouldPingExternalUsage,
} from "../utils/appUsageSession";

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
  const activeAppRef = useRef<ActiveAppUsage | null>(null);

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
      // polling primeiro: handshake Engine.IO estável atrás do nginx; depois upgrade WS
      transports: ["polling", "websocket"],
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
      socket.emit("auth.refresh", { token });
    }
  }, [token]);

  useEffect(() => {
    const socket = socketRef.current;
    if (!socket || !token || token.length < 20) return;

    const emitAppClose = (appId?: string) => {
      if (!socket.connected) return;
      socket.emit("app_usage.close", appId ? { appId } : {});
    };

    const clearActiveApp = (appId?: string) => {
      const current = activeAppRef.current;
      if (appId && current?.appId !== appId) return;

      const closingId = appId ?? current?.appId;
      activeAppRef.current = null;
      emitAppClose(closingId);
    };

    const syncExternalSession = () => {
      const active = activeAppRef.current;
      if (!active?.external) return;

      if (shouldCloseExternalUsage(active)) {
        clearActiveApp(active.appId);
      }
    };

    const emitUsagePing = () => {
      if (!socket.connected) return;

      socket.emit("presence.ping");

      syncExternalSession();

      const activeApp = activeAppRef.current;
      if (!activeApp?.appId) return;

      if (!shouldPingExternalUsage(activeApp)) return;

      socket.emit("app_usage.ping", {
        appId: activeApp.appId,
        routePath: activeApp.routePath,
      });
    };

    const emitAppOpen = (active: ActiveAppUsage) => {
      if (!socket.connected) return;

      socket.emit("app_usage.open", {
        appId: active.appId,
        routePath: active.routePath,
      });
    };

    const onConnect = () => {
      const activeApp = activeAppRef.current;
      if (!activeApp?.appId) {
        emitUsagePing();
        return;
      }

      if (activeApp.external && shouldCloseExternalUsage(activeApp)) {
        clearActiveApp(activeApp.appId);
        emitUsagePing();
        return;
      }

      emitAppOpen(activeApp);
      emitUsagePing();
    };

    const onVisibilityChange = () => {
      const active = activeAppRef.current;
      if (!active?.external) return;

      if (document.visibilityState === "hidden") {
        active.leftPortal = true;
        emitUsagePing();
        return;
      }

      syncExternalSession();
    };

    const onAppOpened = (event: Event) => {
      const custom = event as CustomEvent<AppUsageOpenDetail>;
      const appId = custom.detail?.appId;
      const routePath = custom.detail?.routePath;
      const external = custom.detail?.external;

      if (!appId) return;

      activeAppRef.current = {
        appId,
        routePath: routePath || "/",
        external,
        openedAt: external ? Date.now() : undefined,
        leftPortal: false,
      };

      emitAppOpen(activeAppRef.current);
      emitUsagePing();
    };

    const onAppClosed = (event: Event) => {
      const custom = event as CustomEvent<AppUsageCloseDetail>;
      clearActiveApp(custom.detail?.appId);
    };

    socket.on("connect", onConnect);
    document.addEventListener("visibilitychange", onVisibilityChange);
    window.addEventListener(APP_USAGE_OPEN_EVENT, onAppOpened);
    window.addEventListener(APP_USAGE_CLOSE_EVENT, onAppClosed);

    const intervalId = window.setInterval(emitUsagePing, 45_000);

    return () => {
      socket.off("connect", onConnect);
      document.removeEventListener("visibilitychange", onVisibilityChange);
      window.removeEventListener(APP_USAGE_OPEN_EVENT, onAppOpened);
      window.removeEventListener(APP_USAGE_CLOSE_EVENT, onAppClosed);
      window.clearInterval(intervalId);
    };
  }, [token]);

  return socketRef;
};
