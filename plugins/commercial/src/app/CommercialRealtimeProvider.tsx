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
import { usePortfolioScope } from "./PortfolioScopeContext";
import { lookupDirectoryUsers } from "../api/commercialPortfolioApi";
import {
  buildCommercialRealtimeWsUrl,
  isGenericActorDisplayName,
  parseCommercialRealtimeEvent,
  portfolioEventTouchesId,
  resolvePortfolioNotification,
  resolveWorklistNotification,
  type CommercialPortfolioChangedEvent,
  type CommercialWorklistChangedEvent,
} from "../constants/realtime";
import { formatDirectoryUserLabel } from "../shared/directoryUserLabel";

const PING_MS = 25_000;
const RECONNECT_MS = 4_000;

type WorklistChangedHandler = (event: CommercialWorklistChangedEvent) => void;
type PortfolioChangedHandler = (event: CommercialPortfolioChangedEvent) => void;

type CommercialRealtimeContextValue = {
  connected: boolean;
  connectionError: string | null;
  subscribeWorklistChanged: (handler: WorklistChangedHandler) => () => void;
  subscribePortfolioChanged: (handler: PortfolioChangedHandler) => () => void;
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
  const worklistHandlersRef = useRef(new Set<WorklistChangedHandler>());
  const portfolioHandlersRef = useRef(new Set<PortfolioChangedHandler>());
  const getAccessTokenRef = useRef(getAccessToken);

  const [connected, setConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  useEffect(() => {
    getAccessTokenRef.current = getAccessToken;
  }, [getAccessToken]);

  const subscribeWorklistChanged = useCallback((handler: WorklistChangedHandler) => {
    worklistHandlersRef.current.add(handler);
    return () => {
      worklistHandlersRef.current.delete(handler);
    };
  }, []);

  const subscribePortfolioChanged = useCallback((handler: PortfolioChangedHandler) => {
    portfolioHandlersRef.current.add(handler);
    return () => {
      portfolioHandlersRef.current.delete(handler);
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
        if (!event) return;
        if (event.type === "worklist.changed") {
          for (const handler of worklistHandlersRef.current) {
            handler(event);
          }
          return;
        }
        if (event.type === "portfolio.changed") {
          for (const handler of portfolioHandlersRef.current) {
            handler(event);
          }
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
    subscribePortfolioChanged,
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
 * Refetch silencioso quando chega `portfolio.changed` (lista admin / detalhe / Minha Carteira).
 * Opcionalmente filtra por `portfolioId` aberto.
 */
export function useCommercialPortfolioSync(
  onChanged: (event: CommercialPortfolioChangedEvent) => void,
  options?: { enabled?: boolean; portfolioId?: string | null },
) {
  const { subscribePortfolioChanged } = useCommercialRealtime();
  const onChangedRef = useRef(onChanged);
  const portfolioId = options?.portfolioId ?? null;
  const enabled = options?.enabled ?? true;

  useEffect(() => {
    onChangedRef.current = onChanged;
  }, [onChanged]);

  useEffect(() => {
    if (!enabled) return;
    let timer: number | null = null;
    const unsubscribe = subscribePortfolioChanged((event) => {
      if (portfolioId && !portfolioEventTouchesId(event, portfolioId)) {
        return;
      }
      if (timer != null) window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        timer = null;
        onChangedRef.current(event);
      }, 400);
    });
    return () => {
      unsubscribe();
      if (timer != null) window.clearTimeout(timer);
    };
  }, [enabled, portfolioId, subscribePortfolioChanged]);
}

/**
 * Toast in-app para eventos WS de outros clientes (anti-eco por clientId).
 * Worklist: mensagem personalizada por audiência.
 * Portfolio: usa notification do servidor / fallback local.
 */
export function useCommercialRealtimeNotices(enabled = true) {
  const { subscribeWorklistChanged, subscribePortfolioChanged } = useCommercialRealtime();
  const { notifyInfo, notifySuccess, notifyWarning } = useCommercialFloatingNotice();
  const { myPortfolio, currentUserId } = usePortfolioScope();
  const clientId = getCommercialClientId();
  const resolvedUserId = currentUserId ?? myPortfolio?.user_id ?? null;

  useEffect(() => {
    if (!enabled) return;

    const publishWorklist = (event: CommercialWorklistChangedEvent) => {
      const payload = resolveWorklistNotification(event, resolvedUserId);
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
    };

    const unsubWorklist = subscribeWorklistChanged((event) => {
      if (event.actorClientId && event.actorClientId === clientId) {
        return;
      }

      const needActor = isGenericActorDisplayName(event.actorDisplayName);
      const needAssignee = isGenericActorDisplayName(event.assigneeDisplayName);
      const ids = [
        needActor ? (event.actorUserId || "").trim() : "",
        needAssignee ? (event.assigneeUserIds?.[0] || "").trim() : "",
      ].filter(Boolean);

      if (ids.length === 0) {
        publishWorklist(event);
        return;
      }

      void lookupDirectoryUsers(ids)
        .then((items) => {
          const byId = new Map(
            items.filter((item) => item?.id).map((item) => [item.id, item]),
          );
          let next = event;
          if (needActor && event.actorUserId) {
            const label = formatDirectoryUserLabel(byId.get(event.actorUserId) || {});
            if (label) {
              next = { ...next, actorDisplayName: label };
            }
          }
          if (needAssignee && event.assigneeUserIds?.[0]) {
            const label = formatDirectoryUserLabel(
              byId.get(event.assigneeUserIds[0]) || {},
            );
            if (label) {
              next = { ...next, assigneeDisplayName: label };
            }
          }
          publishWorklist(next);
        })
        .catch(() => {
          publishWorklist(event);
        });
    });

    const publishPortfolio = (event: CommercialPortfolioChangedEvent) => {
      const payload = resolvePortfolioNotification(event);
      const pid = (event.portfolioId || "").trim() || "portfolio";
      const options = {
        title: payload.title,
        id: `cm-rt-pf-${pid}-${event.reason}`,
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
    };

    const unsubPortfolio = subscribePortfolioChanged((event) => {
      if (event.actorClientId && event.actorClientId === clientId) {
        return;
      }

      const needActor = isGenericActorDisplayName(event.actorDisplayName);
      const actorId = needActor ? (event.actorUserId || "").trim() : "";
      if (!actorId) {
        publishPortfolio(event);
        return;
      }

      void lookupDirectoryUsers([actorId])
        .then((items) => {
          const label = formatDirectoryUserLabel(items[0] || {});
          publishPortfolio(
            label ? { ...event, actorDisplayName: label } : event,
          );
        })
        .catch(() => {
          publishPortfolio(event);
        });
    });

    return () => {
      unsubWorklist();
      unsubPortfolio();
    };
  }, [
    clientId,
    resolvedUserId,
    enabled,
    notifyInfo,
    notifySuccess,
    notifyWarning,
    subscribeWorklistChanged,
    subscribePortfolioChanged,
  ]);
}
