import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { useMyRequestsFloatingNotice } from "./MyRequestsFloatingNoticeProvider";
import { getMyRequestsClientId } from "./myRequestsClientId";
import {
  buildMyRequestsRealtimeWsUrl,
  buildRequestSubscribePayload,
  buildRequestUnsubscribePayload,
  parseMyRequestsRealtimeEvent,
  resolveRemoteNotification,
  type MyRequestsRealtimeEvent,
} from "../constants/realtime";

const PING_MS = 25_000;
const RECONNECT_MS = 4_000;
const SYNC_DEBOUNCE_MS = 400;

type CreatedHandler = (
  event: Extract<MyRequestsRealtimeEvent, { type: "request.created" }>,
) => void;
type ChangedHandler = (
  event: Extract<MyRequestsRealtimeEvent, { type: "request.changed" }>,
) => void;
type TimelineHandler = (
  event: Extract<MyRequestsRealtimeEvent, { type: "request.timeline" }>,
) => void;

type MyRequestsRealtimeContextValue = {
  connected: boolean;
  connectionError: string | null;
  subscribeRequestCreated: (handler: CreatedHandler) => () => void;
  subscribeRequestChanged: (handler: ChangedHandler) => () => void;
  subscribeRequestTimeline: (handler: TimelineHandler) => () => void;
  joinRequestRoom: (requestId: string) => void;
  leaveRequestRoom: (requestId: string) => void;
};

const MyRequestsRealtimeContext =
  createContext<MyRequestsRealtimeContextValue | null>(null);

type MyRequestsRealtimeProviderProps = {
  getAccessToken?: () => string | undefined;
  enabled?: boolean;
  children: ReactNode;
};

export function MyRequestsRealtimeProvider({
  getAccessToken,
  enabled = true,
  children,
}: MyRequestsRealtimeProviderProps) {
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const pingTimerRef = useRef<number | null>(null);
  const clientIdRef = useRef(getMyRequestsClientId());
  const createdHandlersRef = useRef(new Set<CreatedHandler>());
  const changedHandlersRef = useRef(new Set<ChangedHandler>());
  const timelineHandlersRef = useRef(new Set<TimelineHandler>());
  const desiredRequestIdsRef = useRef(new Set<string>());
  const getAccessTokenRef = useRef(getAccessToken);

  const [connected, setConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  useEffect(() => {
    getAccessTokenRef.current = getAccessToken;
  }, [getAccessToken]);

  const subscribeRequestCreated = useCallback((handler: CreatedHandler) => {
    createdHandlersRef.current.add(handler);
    return () => {
      createdHandlersRef.current.delete(handler);
    };
  }, []);

  const subscribeRequestChanged = useCallback((handler: ChangedHandler) => {
    changedHandlersRef.current.add(handler);
    return () => {
      changedHandlersRef.current.delete(handler);
    };
  }, []);

  const subscribeRequestTimeline = useCallback((handler: TimelineHandler) => {
    timelineHandlersRef.current.add(handler);
    return () => {
      timelineHandlersRef.current.delete(handler);
    };
  }, []);

  const joinRequestRoom = useCallback((requestId: string) => {
    const id = requestId.trim();
    if (!id) return;
    desiredRequestIdsRef.current.add(id);
    const socket = socketRef.current;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(buildRequestSubscribePayload(id));
    }
  }, []);

  const leaveRequestRoom = useCallback((requestId: string) => {
    const id = requestId.trim();
    if (!id) return;
    desiredRequestIdsRef.current.delete(id);
    const socket = socketRef.current;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(buildRequestUnsubscribePayload(id));
    }
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
          buildMyRequestsRealtimeWsUrl({
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
        for (const requestId of desiredRequestIdsRef.current) {
          socket.send(buildRequestSubscribePayload(requestId));
        }
        pingTimerRef.current = window.setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) {
            socket.send("ping");
          }
        }, PING_MS);
      };

      socket.onmessage = (message) => {
        if (typeof message.data !== "string") return;
        const event = parseMyRequestsRealtimeEvent(message.data);
        if (!event) return;
        if (event.type === "request.created") {
          for (const handler of createdHandlersRef.current) handler(event);
          return;
        }
        if (event.type === "request.changed") {
          for (const handler of changedHandlersRef.current) handler(event);
          return;
        }
        if (event.type === "request.timeline") {
          for (const handler of timelineHandlersRef.current) handler(event);
        }
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

  useMyRequestsRemoteToasts({
    enabled,
    subscribeRequestCreated,
    subscribeRequestChanged,
    subscribeRequestTimeline,
  });

  const value: MyRequestsRealtimeContextValue = {
    connected,
    connectionError,
    subscribeRequestCreated,
    subscribeRequestChanged,
    subscribeRequestTimeline,
    joinRequestRoom,
    leaveRequestRoom,
  };

  return (
    <MyRequestsRealtimeContext.Provider value={value}>
      {children}
    </MyRequestsRealtimeContext.Provider>
  );
}

export function useMyRequestsRealtime(): MyRequestsRealtimeContextValue {
  const ctx = useContext(MyRequestsRealtimeContext);
  if (!ctx) {
    throw new Error(
      "useMyRequestsRealtime must be used within MyRequestsRealtimeProvider",
    );
  }
  return ctx;
}

function useDebouncedSync(
  subscribe: (handler: () => void) => () => void,
  onChanged: () => void,
  enabled: boolean,
) {
  const onChangedRef = useRef(onChanged);
  useEffect(() => {
    onChangedRef.current = onChanged;
  }, [onChanged]);

  useEffect(() => {
    if (!enabled) return;
    let timer: number | null = null;
    const unsubscribe = subscribe(() => {
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
  }, [enabled, subscribe]);
}

export function useMyRequestsListSync(onChanged: () => void, enabled = true) {
  const { subscribeRequestCreated, subscribeRequestChanged } =
    useMyRequestsRealtime();
  useDebouncedSync(subscribeRequestCreated, onChanged, enabled);
  useDebouncedSync(subscribeRequestChanged, onChanged, enabled);
}

export function useMyRequestsDetailSync(
  requestId: string | null | undefined,
  handlers: {
    onChanged?: () => void;
    onTimeline?: (reason?: string) => void;
  },
  enabled = true,
) {
  const {
    joinRequestRoom,
    leaveRequestRoom,
    subscribeRequestChanged,
    subscribeRequestTimeline,
  } = useMyRequestsRealtime();
  const onChangedRef = useRef(handlers.onChanged);
  const onTimelineRef = useRef(handlers.onTimeline);

  useEffect(() => {
    onChangedRef.current = handlers.onChanged;
    onTimelineRef.current = handlers.onTimeline;
  }, [handlers.onChanged, handlers.onTimeline]);

  useEffect(() => {
    const id = (requestId || "").trim();
    if (!enabled || !id) return;
    joinRequestRoom(id);
    return () => leaveRequestRoom(id);
  }, [enabled, joinRequestRoom, leaveRequestRoom, requestId]);

  useEffect(() => {
    const id = (requestId || "").trim();
    if (!enabled || !id) return;
    let timer: number | null = null;
    const unsubscribe = subscribeRequestChanged((event) => {
      if ((event.requestId || "").trim() !== id) return;
      if (timer != null) window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        timer = null;
        onChangedRef.current?.();
      }, SYNC_DEBOUNCE_MS);
    });
    return () => {
      unsubscribe();
      if (timer != null) window.clearTimeout(timer);
    };
  }, [enabled, requestId, subscribeRequestChanged]);

  useEffect(() => {
    const id = (requestId || "").trim();
    if (!enabled || !id) return;
    let timer: number | null = null;
    const unsubscribe = subscribeRequestTimeline((event) => {
      if ((event.requestId || "").trim() !== id) return;
      if (timer != null) window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        timer = null;
        onTimelineRef.current?.(event.reason);
      }, SYNC_DEBOUNCE_MS);
    });
    return () => {
      unsubscribe();
      if (timer != null) window.clearTimeout(timer);
    };
  }, [enabled, requestId, subscribeRequestTimeline]);
}

function useMyRequestsRemoteToasts(options: {
  enabled: boolean;
  subscribeRequestCreated: (handler: CreatedHandler) => () => void;
  subscribeRequestChanged: (handler: ChangedHandler) => () => void;
  subscribeRequestTimeline: (handler: TimelineHandler) => () => void;
}) {
  const { notifyInfo, notifySuccess, notifyWarning, notifyError } =
    useMyRequestsFloatingNotice();
  const clientId = getMyRequestsClientId();
  const {
    enabled,
    subscribeRequestCreated,
    subscribeRequestChanged,
    subscribeRequestTimeline,
  } = options;
  const recentToastKeysRef = useRef<Map<string, number>>(new Map());

  useEffect(() => {
    if (!enabled) return;

    const show = (
      event: Extract<
        MyRequestsRealtimeEvent,
        { type: "request.created" | "request.changed" | "request.timeline" }
      >,
    ) => {
      if (event.actorClientId && event.actorClientId === clientId) return;
      const notice = resolveRemoteNotification(event);
      if (!notice) return;
      const dedupeKey = [
        event.type,
        event.requestId || "",
        event.reason || "",
        event.status || "",
        notice.title,
        notice.message,
      ].join("|");
      const now = Date.now();
      const last = recentToastKeysRef.current.get(dedupeKey) || 0;
      if (now - last < 2000) return;
      recentToastKeysRef.current.set(dedupeKey, now);
      for (const [key, ts] of recentToastKeysRef.current) {
        if (now - ts > 10_000) recentToastKeysRef.current.delete(key);
      }
      if (notice.variant === "success") {
        notifySuccess(notice.message, { title: notice.title, id: dedupeKey });
        return;
      }
      if (notice.variant === "warning") {
        notifyWarning(notice.message, { title: notice.title, id: dedupeKey });
        return;
      }
      if (notice.variant === "error") {
        notifyError(notice.message, { title: notice.title, id: dedupeKey });
        return;
      }
      notifyInfo(notice.message, { title: notice.title, id: dedupeKey });
    };

    const unsubs = [
      subscribeRequestCreated(show),
      subscribeRequestChanged(show),
      subscribeRequestTimeline(show),
    ];
    return () => {
      for (const unsub of unsubs) unsub();
    };
  }, [
    clientId,
    enabled,
    notifyError,
    notifyInfo,
    notifySuccess,
    notifyWarning,
    subscribeRequestChanged,
    subscribeRequestCreated,
    subscribeRequestTimeline,
  ]);
}
