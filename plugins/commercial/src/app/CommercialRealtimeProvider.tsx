import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

import {
  fanPresenceUpdated,
  subscribePresenceWithReplay,
} from "./commercialPresenceSubscribe";
import { getCommercialClientId } from "./commercialClientId";
import { useCommercialFloatingNotice } from "./CommercialFloatingNoticeProvider";
import { usePortfolioScope } from "./PortfolioScopeContext";
import { lookupDirectoryUsers } from "../api/commercialPortfolioApi";
import {
  buildInteractionRoomSubscribePayload,
  buildInteractionRoomUnsubscribePayload,
  interactionRoomEventTouchesRoom,
  isInteractionRoomEventType,
  type CommercialInteractionRoomEvent,
} from "../constants/interactionRoomRealtime";
import {
  buildCommercialRealtimeWsUrl,
  isGenericActorDisplayName,
  parseCommercialRealtimeEvent,
  accountEventTouchesCustomer,
  portfolioEventTouchesId,
  resolveAccountNotification,
  resolvePortfolioNotification,
  resolveReadyToInvoiceNotification,
  resolveWorklistNotification,
  type CommercialAccountChangedEvent,
  type CommercialOrdersReadyToInvoiceEvent,
  type CommercialPortfolioChangedEvent,
  type CommercialPresenceUpdatedEvent,
  type CommercialWorklistChangedEvent,
} from "../constants/realtime";
import { formatDirectoryUserLabel } from "../shared/directoryUserLabel";

const PING_MS = 25_000;
const RECONNECT_MS = 4_000;

type WorklistChangedHandler = (event: CommercialWorklistChangedEvent) => void;
type PortfolioChangedHandler = (event: CommercialPortfolioChangedEvent) => void;
type AccountChangedHandler = (event: CommercialAccountChangedEvent) => void;
type PresenceUpdatedHandler = (event: CommercialPresenceUpdatedEvent) => void;
type ReadyToInvoiceHandler = (event: CommercialOrdersReadyToInvoiceEvent) => void;
type InteractionRoomEventHandler = (event: CommercialInteractionRoomEvent) => void;

type CommercialRealtimeContextValue = {
  connected: boolean;
  connectionError: string | null;
  subscribeWorklistChanged: (handler: WorklistChangedHandler) => () => void;
  subscribePortfolioChanged: (handler: PortfolioChangedHandler) => () => void;
  subscribeAccountChanged: (handler: AccountChangedHandler) => () => void;
  subscribePresenceUpdated: (handler: PresenceUpdatedHandler) => () => void;
  subscribeReadyToInvoice: (handler: ReadyToInvoiceHandler) => () => void;
  joinInteractionRoom: (roomId: string) => void;
  leaveInteractionRoom: (roomId: string) => void;
  subscribeInteractionRoomEvents: (
    handler: InteractionRoomEventHandler,
  ) => () => void;
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
  const accountHandlersRef = useRef(new Set<AccountChangedHandler>());
  const presenceHandlersRef = useRef(new Set<PresenceUpdatedHandler>());
  const readyToInvoiceHandlersRef = useRef(new Set<ReadyToInvoiceHandler>());
  const interactionRoomHandlersRef = useRef(new Set<InteractionRoomEventHandler>());
  const desiredInteractionRoomIdsRef = useRef(new Set<string>());
  const lastPresenceRef = useRef<CommercialPresenceUpdatedEvent | null>(null);
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

  const subscribeAccountChanged = useCallback((handler: AccountChangedHandler) => {
    accountHandlersRef.current.add(handler);
    return () => {
      accountHandlersRef.current.delete(handler);
    };
  }, []);

  const subscribePresenceUpdated = useCallback((handler: PresenceUpdatedHandler) => {
    return subscribePresenceWithReplay(lastPresenceRef, presenceHandlersRef.current, handler);
  }, []);

  const subscribeReadyToInvoice = useCallback((handler: ReadyToInvoiceHandler) => {
    readyToInvoiceHandlersRef.current.add(handler);
    return () => {
      readyToInvoiceHandlersRef.current.delete(handler);
    };
  }, []);

  const sendInteractionRoomProtocol = useCallback((payload: string) => {
    const socket = socketRef.current;
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(payload);
    }
  }, []);

  const joinInteractionRoom = useCallback(
    (roomId: string) => {
      const id = roomId.trim();
      if (!id) return;
      desiredInteractionRoomIdsRef.current.add(id);
      sendInteractionRoomProtocol(buildInteractionRoomSubscribePayload(id));
    },
    [sendInteractionRoomProtocol],
  );

  const leaveInteractionRoom = useCallback(
    (roomId: string) => {
      const id = roomId.trim();
      if (!id) return;
      desiredInteractionRoomIdsRef.current.delete(id);
      sendInteractionRoomProtocol(buildInteractionRoomUnsubscribePayload(id));
    },
    [sendInteractionRoomProtocol],
  );

  const subscribeInteractionRoomEvents = useCallback(
    (handler: InteractionRoomEventHandler) => {
      interactionRoomHandlersRef.current.add(handler);
      return () => {
        interactionRoomHandlersRef.current.delete(handler);
      };
    },
    [],
  );

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
        for (const roomId of desiredInteractionRoomIdsRef.current) {
          socket.send(buildInteractionRoomSubscribePayload(roomId));
        }
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
          return;
        }
        if (event.type === "account.changed") {
          for (const handler of accountHandlersRef.current) {
            handler(event);
          }
          return;
        }
        if (event.type === "presence.updated") {
          fanPresenceUpdated(lastPresenceRef, presenceHandlersRef.current, event);
          return;
        }
        if (event.type === "orders.ready_to_invoice") {
          for (const handler of readyToInvoiceHandlersRef.current) {
            handler(event);
          }
          return;
        }
        if (isInteractionRoomEventType(event.type)) {
          const roomEvent = event as CommercialInteractionRoomEvent;
          for (const handler of interactionRoomHandlersRef.current) {
            handler(roomEvent);
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
      const socket = socketRef.current;
      socketRef.current = null;
      if (socket) {
        socket.onclose = null;
        socket.onerror = null;
        socket.onmessage = null;
        socket.onopen = null;
        try {
          socket.close(1000, "commercial-unmount");
        } catch {
          /* ignore */
        }
      }
      setConnected(false);
    };
  }, [enabled]);

  const value: CommercialRealtimeContextValue = {
    connected,
    connectionError,
    subscribeWorklistChanged,
    subscribePortfolioChanged,
    subscribeAccountChanged,
    subscribePresenceUpdated,
    subscribeReadyToInvoice,
    joinInteractionRoom,
    leaveInteractionRoom,
    subscribeInteractionRoomEvents,
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
 * Join/leave `room:{uuid}` no WS existente e escuta eventos `room.*` da sala aberta.
 * Não recarrega a UI sozinho — o host decide o que fazer no `onEvent`.
 */
export function useInteractionRoomSync(
  roomId: string | null | undefined,
  onEvent: (event: CommercialInteractionRoomEvent) => void,
  enabled = true,
) {
  const {
    joinInteractionRoom,
    leaveInteractionRoom,
    subscribeInteractionRoomEvents,
  } = useCommercialRealtime();
  const onEventRef = useRef(onEvent);

  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  useEffect(() => {
    const id = (roomId || "").trim();
    if (!enabled || !id) return;
    joinInteractionRoom(id);
    return () => leaveInteractionRoom(id);
  }, [enabled, roomId, joinInteractionRoom, leaveInteractionRoom]);

  useEffect(() => {
    const id = (roomId || "").trim();
    if (!enabled || !id) return;
    return subscribeInteractionRoomEvents((event) => {
      if (!interactionRoomEventTouchesRoom(event, id)) return;
      onEventRef.current(event);
    });
  }, [enabled, roomId, subscribeInteractionRoomEvents]);
}

/** Refetch badge / lista quando chega `orders.ready_to_invoice`. */
export function useCommercialReadyToInvoiceSync(onChanged: () => void, enabled = true) {
  const { subscribeReadyToInvoice } = useCommercialRealtime();
  const onChangedRef = useRef(onChanged);

  useEffect(() => {
    onChangedRef.current = onChanged;
  }, [onChanged]);

  useEffect(() => {
    if (!enabled) return;
    let timer: number | null = null;
    const unsubscribe = subscribeReadyToInvoice(() => {
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
  }, [enabled, subscribeReadyToInvoice]);
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
 * Refetch silencioso quando chega `account.changed` (contatos / avatar / histórico da conta).
 * Filtra por code/store da conta aberta.
 */
export function useCommercialAccountSync(
  onChanged: (event: CommercialAccountChangedEvent) => void,
  options?: {
    enabled?: boolean;
    customerCode?: string | null;
    customerStore?: string | null;
  },
) {
  const { subscribeAccountChanged } = useCommercialRealtime();
  const onChangedRef = useRef(onChanged);
  const customerCode = options?.customerCode ?? null;
  const customerStore = options?.customerStore ?? null;
  const enabled = options?.enabled ?? true;

  useEffect(() => {
    onChangedRef.current = onChanged;
  }, [onChanged]);

  useEffect(() => {
    if (!enabled) return;
    let timer: number | null = null;
    const unsubscribe = subscribeAccountChanged((event) => {
      if (
        customerCode &&
        customerStore &&
        !accountEventTouchesCustomer(event, customerCode, customerStore)
      ) {
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
  }, [customerCode, customerStore, enabled, subscribeAccountChanged]);
}

/**
 * Presença da Equipe (`presence.updated` — só gestores na sala `team`).
 * UI completa (dot Online) fica em E7.S2.
 */
export function useCommercialPresenceSync(
  onUpdated: (event: CommercialPresenceUpdatedEvent) => void,
  enabled = true,
) {
  const { subscribePresenceUpdated } = useCommercialRealtime();
  const onUpdatedRef = useRef(onUpdated);

  useEffect(() => {
    onUpdatedRef.current = onUpdated;
  }, [onUpdated]);

  useEffect(() => {
    if (!enabled) return;
    return subscribePresenceUpdated((event) => {
      onUpdatedRef.current(event);
    });
  }, [enabled, subscribePresenceUpdated]);
}

/**
 * Toast in-app para eventos WS de outros clientes (anti-eco por clientId).
 * Worklist: mensagem personalizada por audiência.
 * Portfolio: usa notification do servidor / fallback local.
 */
export function useCommercialRealtimeNotices(enabled = true) {
  const {
    subscribeWorklistChanged,
    subscribePortfolioChanged,
    subscribeAccountChanged,
    subscribeReadyToInvoice,
  } = useCommercialRealtime();
  const { notifyInfo, notifySuccess, notifyWarning, notifyError } =
    useCommercialFloatingNotice();
  const { myPortfolio, currentUserId } = usePortfolioScope();
  const clientId = getCommercialClientId();
  const resolvedUserId = currentUserId ?? myPortfolio?.user_id ?? null;

  useEffect(() => {
    if (!enabled) return;

    const publishByVariant = (
      payload: { title: string; message: string; variant: string },
      options: { title: string; id: string; autoDismissMs: number | null },
    ) => {
      if (payload.variant === "success") {
        notifySuccess(payload.message, options);
        return;
      }
      if (payload.variant === "warning") {
        notifyWarning(payload.message, options);
        return;
      }
      if (payload.variant === "error") {
        notifyError(payload.message, options);
        return;
      }
      notifyInfo(payload.message, options);
    };

    const publishWorklist = (event: CommercialWorklistChangedEvent) => {
      const payload = resolveWorklistNotification(event, resolvedUserId);
      publishByVariant(payload, {
        title: payload.title,
        id: `cm-rt-${event.taskId}-${event.reason}`,
        autoDismissMs: 6500,
      });
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
      publishByVariant(payload, {
        title: payload.title,
        id: `cm-rt-pf-${pid}-${event.reason}`,
        autoDismissMs: 6500,
      });
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
          publishPortfolio(label ? { ...event, actorDisplayName: label } : event);
        })
        .catch(() => {
          publishPortfolio(event);
        });
    });

    const publishAccount = (event: CommercialAccountChangedEvent) => {
      const payload = resolveAccountNotification(event);
      const key = `${(event.customerCode || "").trim()}-${(event.customerStore || "").trim()}`;
      publishByVariant(payload, {
        title: payload.title,
        id: `cm-rt-ac-${key}-${event.reason}`,
        autoDismissMs: 6500,
      });
    };

    const unsubAccount = subscribeAccountChanged((event) => {
      if (event.actorClientId && event.actorClientId === clientId) {
        return;
      }
      const needActor = isGenericActorDisplayName(event.actorDisplayName);
      const actorId = needActor ? (event.actorUserId || "").trim() : "";
      if (!actorId) {
        publishAccount(event);
        return;
      }
      void lookupDirectoryUsers([actorId])
        .then((items) => {
          const label = formatDirectoryUserLabel(items[0] || {});
          publishAccount(label ? { ...event, actorDisplayName: label } : event);
        })
        .catch(() => {
          publishAccount(event);
        });
    });

    const unsubReady = subscribeReadyToInvoice((event) => {
      const payload = resolveReadyToInvoiceNotification(event);
      const key = (event.lineKey || `${event.pedido}-${event.linha}` || "r2i").trim();
      publishByVariant(payload, {
        title: payload.title,
        id: `cm-rt-r2i-${key}`,
        autoDismissMs: 6500,
      });
    });

    return () => {
      unsubWorklist();
      unsubPortfolio();
      unsubAccount();
      unsubReady();
    };
  }, [
    clientId,
    resolvedUserId,
    enabled,
    notifyInfo,
    notifySuccess,
    notifyWarning,
    notifyError,
    subscribeWorklistChanged,
    subscribePortfolioChanged,
    subscribeAccountChanged,
    subscribeReadyToInvoice,
  ]);
}
