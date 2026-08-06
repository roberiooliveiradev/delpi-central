import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { getCommercialClientId } from "./commercialClientId";
import { useCommercialFloatingNotice } from "./CommercialFloatingNoticeProvider";
import {
  buildCommercialRealtimeWsUrl,
  fallbackWorklistNotification,
  parseCommercialRealtimeEvent,
  type CommercialWorklistChangedEvent,
} from "../constants/realtime";

const PING_MS = 25_000;
const RECONNECT_MS = 4_000;

type WorklistChangedHandler = (event: CommercialWorklistChangedEvent) => void;

type CommercialRealtimeContextValue = {
  connected: boolean;
  connectionError: string | null;
  subscribeWorklistChanged: (handler: WorklistChangedHandler) => () => void;
};

const CommercialRealtimeContext = createContext<CommercialRealtimeContextValue | null>(null);

type CommercialRealtimeProviderProps = {
  getAccessToken?: () => string | undefined;
  enabled?: boolean;
  children: ReactNode;
};

export function CommercialRealtimeProvider({
  getAccessToken,
  enabled = true,
  children,
}: CommercialRealtimeProviderProps) {
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const pingTimerRef = useRef<number | null>(null);
  const clientIdRef = useRef(getCommercialClientId());
  const handlersRef = useRef(new Set<WorklistChangedHandler>());
  const getAccessTokenRef = useRef(getAccessToken);

  const [connected, setConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  useEffect(() => {
    getAccessTokenRef.current = getAccessToken;
  }, [getAccessToken]);

  const subscribeWorklistChanged = useCallback((handler: WorklistChangedHandler) => {
    handlersRef.current.add(handler);
    return () => {
      handlersRef.current.delete(handler);
    };
  }, []);

  useEffect(() => {
    if (!enabled) {
      setConnected(false);
      setConnectionError(null);
      return;
    }

    let cancelled = false;

    const clearTimers = () => {
      if (reconnectTimerRef.current != null) {
        window.clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      if (pingTimerRef.current != null) {
        window.clearInterval(pingTimerRef.current);
        pingTimerRef.current = null;
      }
    };

    const scheduleReconnect = () => {
      if (cancelled || reconnectTimerRef.current != null) return;
      reconnectTimerRef.current = window.setTimeout(() => {
        reconnectTimerRef.current = null;
        connect();
      }, RECONNECT_MS);
    };

    const connect = () => {
      clearTimers();
      socketRef.current?.close();

      const token = getAccessTokenRef.current?.();
      if (!token) {
        setConnectionError("Sessão não autenticada para tempo real.");
        setConnected(false);
        scheduleReconnect();
        return;
      }

      let socket: WebSocket;
      try {
        socket = new WebSocket(
          buildCommercialRealtimeWsUrl({
            token,
            clientId: clientIdRef.current,
          }),
        );
      } catch {
        setConnectionError("Não foi possível abrir conexão em tempo real.");
        setConnected(false);
        scheduleReconnect();
        return;
      }

      socketRef.current = socket;

      socket.onopen = () => {
        if (cancelled) return;
        setConnectionError(null);
        setConnected(true);
        pingTimerRef.current = window.setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) {
            socket.send("ping");
          }
        }, PING_MS);
      };

      socket.onmessage = (message) => {
        if (typeof message.data !== "string") return;
        const event = parseCommercialRealtimeEvent(message.data);
        if (!event || event.type !== "worklist.changed") return;
        for (const handler of handlersRef.current) {
          handler(event);
        }
      };

      socket.onerror = () => {
        if (cancelled) return;
        setConnectionError("Erro na conexão em tempo real.");
      };

      socket.onclose = () => {
        if (cancelled) return;
        clearTimers();
        setConnected(false);
        scheduleReconnect();
      };
    };

    connect();

    return () => {
      cancelled = true;
      clearTimers();
      socketRef.current?.close();
      socketRef.current = null;
      setConnected(false);
    };
  }, [enabled]);

  const value: CommercialRealtimeContextValue = {
    connected,
    connectionError,
    subscribeWorklistChanged,
  };

  return (
    <CommercialRealtimeContext.Provider value={value}>
      {children}
    </CommercialRealtimeContext.Provider>
  );
}

export function useCommercialRealtime() {
  const ctx = useContext(CommercialRealtimeContext);
  if (!ctx) {
    throw new Error("useCommercialRealtime must be used within CommercialRealtimeProvider");
  }
  return ctx;
}

export function useCommercialWorklistSync(onChanged: () => void, enabled = true) {
  const { subscribeWorklistChanged } = useCommercialRealtime();
  const onChangedRef = useRef(onChanged);

  useEffect(() => {
    onChangedRef.current = onChanged;
  }, [onChanged]);

  useEffect(() => {
    if (!enabled) return;
    let timer: number | null = null;
    const unsubscribe = subscribeWorklistChanged(() => {
      if (timer != null) window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        timer = null;
        onChangedRef.current();
      }, 400);
    });
    return () => {
      unsubscribe();
      if (timer != null) window.clearTimeout(timer);
    };
  }, [enabled, subscribeWorklistChanged]);
}

/**
 * Toast in-app para eventos WS de outros clientes (anti-eco por clientId).
 * Refetch da fila fica em `useCommercialWorklistSync`.
 */
export function useCommercialRealtimeNotices(enabled = true) {
  const { subscribeWorklistChanged } = useCommercialRealtime();
  const { notifyInfo, notifySuccess, notifyWarning } = useCommercialFloatingNotice();
  const clientId = getCommercialClientId();

  useEffect(() => {
    if (!enabled) return;
    return subscribeWorklistChanged((event) => {
      if (event.actorClientId && event.actorClientId === clientId) {
        return;
      }
      const payload =
        event.notification && event.notification.message
          ? event.notification
          : fallbackWorklistNotification(event);
      const options = {
        title: payload.title,
        id: `cm-rt-${event.taskId}-${event.reason}`,
        autoDismissMs: 6500 as number | null,
      };
      if (payload.variant === "success") {
        notifySuccess(payload.message, options);
        return;
      }
      if (payload.variant === "warning") {
        notifyWarning(payload.message, options);
        return;
      }
      notifyInfo(payload.message, options);
    });
  }, [clientId, enabled, notifyInfo, notifySuccess, notifyWarning, subscribeWorklistChanged]);
}
