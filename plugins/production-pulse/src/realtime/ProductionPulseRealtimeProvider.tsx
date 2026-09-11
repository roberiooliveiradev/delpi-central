import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { getProductionPulseClientId } from "./productionPulseClientId";
import {
  buildProductionPulseRealtimeWsUrl,
  isHubRealtimeHint,
  parseProductionPulseRealtimeEvent,
  type ProductionPulseRealtimeEvent,
} from "./constants";

const PING_MS = 25_000;
const RECONNECT_MS = 4_000;
const SYNC_DEBOUNCE_MS = 400;

type HubHintHandler = (
  event: Extract<
    ProductionPulseRealtimeEvent,
    {
      type:
        | "device.updated"
        | "firmware.catalog.updated"
        | "ota.job.updated"
        | "ota.target.updated";
    }
  >,
) => void;

type ProductionPulseRealtimeContextValue = {
  connected: boolean;
  connectionError: string | null;
  subscribeHubHints: (handler: HubHintHandler) => () => void;
};

const ProductionPulseRealtimeContext =
  createContext<ProductionPulseRealtimeContextValue | null>(null);

type ProductionPulseRealtimeProviderProps = {
  getAccessToken?: () => string | undefined;
  enabled?: boolean;
  children: ReactNode;
};

export function ProductionPulseRealtimeProvider({
  getAccessToken,
  enabled = true,
  children,
}: ProductionPulseRealtimeProviderProps) {
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const pingTimerRef = useRef<number | null>(null);
  const clientIdRef = useRef(getProductionPulseClientId());
  const hubHandlersRef = useRef(new Set<HubHintHandler>());
  const getAccessTokenRef = useRef(getAccessToken);

  const [connected, setConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  useEffect(() => {
    getAccessTokenRef.current = getAccessToken;
  }, [getAccessToken]);

  const subscribeHubHints = useCallback((handler: HubHintHandler) => {
    hubHandlersRef.current.add(handler);
    return () => {
      hubHandlersRef.current.delete(handler);
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
          buildProductionPulseRealtimeWsUrl({
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
        const event = parseProductionPulseRealtimeEvent(message.data);
        if (!event || !isHubRealtimeHint(event)) return;
        for (const handler of hubHandlersRef.current) handler(event);
      };

      socket.onclose = () => {
        if (cancelled) return;
        setConnected(false);
        clearTimers();
        scheduleReconnect();
      };

      socket.onerror = () => {
        setConnectionError("Falha na conexão em tempo real.");
      };
    };

    connect();

    return () => {
      cancelled = true;
      clearTimers();
      socketRef.current?.close();
      socketRef.current = null;
    };
  }, [enabled]);

  const value: ProductionPulseRealtimeContextValue = {
    connected,
    connectionError,
    subscribeHubHints,
  };

  return (
    <ProductionPulseRealtimeContext.Provider value={value}>
      {children}
    </ProductionPulseRealtimeContext.Provider>
  );
}

export function useProductionPulseRealtime(): ProductionPulseRealtimeContextValue {
  const ctx = useContext(ProductionPulseRealtimeContext);
  if (!ctx) {
    throw new Error(
      "useProductionPulseRealtime must be used within ProductionPulseRealtimeProvider",
    );
  }
  return ctx;
}

export function useProductionPulseHubSync(
  onChanged: () => void,
  enabled = true,
) {
  const { subscribeHubHints } = useProductionPulseRealtime();
  const onChangedRef = useRef(onChanged);

  useEffect(() => {
    onChangedRef.current = onChanged;
  }, [onChanged]);

  useEffect(() => {
    if (!enabled) return;
    let timer: number | null = null;
    const unsubscribe = subscribeHubHints(() => {
      if (timer != null) window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        timer = null;
        onChangedRef.current();
      }, SYNC_DEBOUNCE_MS);
    });
    return () => {
      unsubscribe();
      if (timer != null) window.clearTimeout(timer);
    };
  }, [enabled, subscribeHubHints]);
}

export function useProductionPulseOtaTargetSync(
  onTargetHint: () => void,
  enabled = true,
) {
  const { subscribeHubHints } = useProductionPulseRealtime();
  const onTargetHintRef = useRef(onTargetHint);

  useEffect(() => {
    onTargetHintRef.current = onTargetHint;
  }, [onTargetHint]);

  useEffect(() => {
    if (!enabled) return;
    let timer: number | null = null;
    const unsubscribe = subscribeHubHints((event) => {
      if (event.type !== "ota.target.updated" && event.type !== "ota.job.updated") {
        return;
      }
      if (timer != null) window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        timer = null;
        onTargetHintRef.current();
      }, SYNC_DEBOUNCE_MS);
    });
    return () => {
      unsubscribe();
      if (timer != null) window.clearTimeout(timer);
    };
  }, [enabled, subscribeHubHints]);
}
