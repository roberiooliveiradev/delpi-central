import { useCallback, useEffect, useRef, useState } from "react";

import type { CollaborationEntityType, CollaborationPresencePayload } from "../data/api/transformometroCollaborationApi";
import {
  clearCollaborationPresence,
  clearCollaborationPresenceKeepalive,
} from "../data/api/transformometroCollaborationApi";
import {
  buildTransformometroRealtimeWsUrl,
  type TransformometroEntityUpdatedEvent,
  type TransformometroLockResultEvent,
  type TransformometroRealtimeOutbound,
} from "../constants/realtime";
import { getTransformometroClientId } from "../utils/clientId";

const PING_MS = 25_000;
const RECONNECT_MS = 4_000;
const LOCK_RESULT_TIMEOUT_MS = 12_000;

type LockResultData = TransformometroLockResultEvent["data"];

type Options = {
  entityType: CollaborationEntityType;
  entityId: string;
  getAccessToken?: () => string | undefined;
  enabled?: boolean;
  onPresenceUpdated?: (presence: CollaborationPresencePayload) => void;
  onEntityUpdated?: (event: TransformometroEntityUpdatedEvent) => void;
  onLockResult?: (event: TransformometroLockResultEvent) => void;
  onRealtimeError?: (message: string, sectionKey?: string | null) => void;
};

export function useTransformometroRealtime({
  entityType,
  entityId,
  getAccessToken,
  enabled = true,
  onPresenceUpdated,
  onEntityUpdated,
  onLockResult,
  onRealtimeError,
}: Options) {
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const pingTimerRef = useRef<number | null>(null);
  const clientIdRef = useRef(getTransformometroClientId());
  const pendingLockRef = useRef<
    Map<string, { resolve: (value: LockResultData) => void; reject: (reason: Error) => void; timer: number }>
  >(new Map());

  const onPresenceUpdatedRef = useRef(onPresenceUpdated);
  const onEntityUpdatedRef = useRef(onEntityUpdated);
  const onLockResultRef = useRef(onLockResult);
  const onRealtimeErrorRef = useRef(onRealtimeError);
  const getAccessTokenRef = useRef(getAccessToken);

  const [connected, setConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  useEffect(() => {
    onPresenceUpdatedRef.current = onPresenceUpdated;
  }, [onPresenceUpdated]);

  useEffect(() => {
    onEntityUpdatedRef.current = onEntityUpdated;
  }, [onEntityUpdated]);

  useEffect(() => {
    onLockResultRef.current = onLockResult;
  }, [onLockResult]);

  useEffect(() => {
    onRealtimeErrorRef.current = onRealtimeError;
  }, [onRealtimeError]);

  useEffect(() => {
    getAccessTokenRef.current = getAccessToken;
  }, [getAccessToken]);

  const clearPendingLocks = useCallback((reason: string) => {
    for (const pending of pendingLockRef.current.values()) {
      window.clearTimeout(pending.timer);
      pending.reject(new Error(reason));
    }
    pendingLockRef.current.clear();
  }, []);

  const sendMessage = useCallback((message: TransformometroRealtimeOutbound | "ping"): boolean => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return false;
    }
    if (message === "ping") {
      socket.send("ping");
      return true;
    }
    socket.send(JSON.stringify(message));
    return true;
  }, []);

  const requestPresence = useCallback(() => {
    sendMessage({ type: "presence.request" });
  }, [sendMessage]);

  const sendHeartbeat = useCallback(
    (sectionKey: string, mode: "viewing" | "editing") => {
      return sendMessage({
        type: "presence.heartbeat",
        sectionKey,
        mode,
      });
    },
    [sendMessage]
  );

  const acquireLock = useCallback(
    (sectionKey: string): Promise<LockResultData | null> => {
      const socket = socketRef.current;
      if (!socket || socket.readyState !== WebSocket.OPEN) {
        return Promise.resolve(null);
      }

      return new Promise((resolve, reject) => {
        const existing = pendingLockRef.current.get(sectionKey);
        if (existing) {
          window.clearTimeout(existing.timer);
          existing.reject(new Error("Nova tentativa de trava substituiu a anterior."));
        }

        const timer = window.setTimeout(() => {
          pendingLockRef.current.delete(sectionKey);
          reject(new Error("Tempo esgotado ao adquirir trava em tempo real."));
        }, LOCK_RESULT_TIMEOUT_MS);

        pendingLockRef.current.set(sectionKey, { resolve, reject, timer });

        if (!sendMessage({ type: "lock.acquire", sectionKey })) {
          window.clearTimeout(timer);
          pendingLockRef.current.delete(sectionKey);
          resolve(null);
        }
      });
    },
    [sendMessage]
  );

  const releaseLock = useCallback(
    (sectionKey: string) => {
      return sendMessage({ type: "lock.release", sectionKey });
    },
    [sendMessage]
  );

  const leavePresence = useCallback(() => {
    return sendMessage({ type: "presence.leave" });
  }, [sendMessage]);

  const clearPresence = useCallback(() => {
    if (sendMessage({ type: "presence.leave" })) {
      return;
    }
    if (!entityId) return;
    void clearCollaborationPresence(entityType, entityId, () => getAccessTokenRef.current?.());
  }, [entityId, entityType, sendMessage]);

  useEffect(() => {
    if (!enabled || !entityId) return;

    const onPageHide = () => {
      const token = getAccessTokenRef.current?.();
      if (!token) return;
      if (socketRef.current?.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({ type: "presence.leave" }));
      }
      clearCollaborationPresenceKeepalive(entityType, entityId, token);
    };

    window.addEventListener("pagehide", onPageHide);
    return () => window.removeEventListener("pagehide", onPageHide);
  }, [enabled, entityId, entityType]);

  useEffect(() => {
    if (!enabled || !entityId) {
      setConnected(false);
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
      clearPendingLocks("Conexão em tempo real reiniciada.");
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
          buildTransformometroRealtimeWsUrl({
            entityType,
            entityId,
            token,
            clientId: clientIdRef.current,
          })
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
        setConnected(true);
        setConnectionError(null);
        sendMessage({ type: "presence.request" });
        pingTimerRef.current = window.setInterval(() => {
          sendMessage("ping");
        }, PING_MS);
      };

      socket.onmessage = (event) => {
        if (cancelled) return;
        try {
          const payload = JSON.parse(String(event.data)) as {
            type?: string;
            data?: CollaborationPresencePayload;
            entityType?: CollaborationEntityType;
            entityId?: string;
            action?: string;
            sectionKey?: string | null;
            actorUserId?: string | null;
            message?: string;
            payload?: Record<string, unknown>;
          };

          if (payload.type === "connected") {
            sendMessage({ type: "presence.request" });
            return;
          }

          if (payload.type === "presence.updated" && payload.data) {
            if (
              payload.entityType &&
              payload.entityId &&
              (payload.entityType !== entityType || payload.entityId !== entityId)
            ) {
              return;
            }
            onPresenceUpdatedRef.current?.(payload.data);
            return;
          }

          if (payload.type === "entity.updated" && payload.entityType && payload.entityId) {
            onEntityUpdatedRef.current?.({
              type: "entity.updated",
              entityType: payload.entityType,
              entityId: payload.entityId,
              action: payload.action ?? "updated",
              sectionKey: payload.sectionKey,
              actorUserId: payload.actorUserId,
              payload: payload.payload,
            });
            return;
          }

          if (payload.type === "lock.result") {
            const sectionKey = payload.sectionKey ?? "";
            const lockData = (payload.data ?? {}) as LockResultData;
            const pending = pendingLockRef.current.get(sectionKey);
            if (pending) {
              window.clearTimeout(pending.timer);
              pendingLockRef.current.delete(sectionKey);
              pending.resolve(lockData);
            }
            onLockResultRef.current?.({
              type: "lock.result",
              entityType: payload.entityType ?? entityType,
              entityId: payload.entityId ?? entityId,
              sectionKey: payload.sectionKey,
              data: lockData,
            });
            return;
          }

          if (payload.type === "error" && payload.message) {
            onRealtimeErrorRef.current?.(payload.message, payload.sectionKey);
          }
        } catch {
          /* ignore malformed payloads */
        }
      };

      socket.onerror = () => {
        if (cancelled) return;
        setConnectionError("Falha na conexão em tempo real.");
      };

      socket.onclose = () => {
        if (cancelled) return;
        setConnected(false);
        clearTimers();
        clearPendingLocks("Conexão em tempo real encerrada.");
        scheduleReconnect();
      };
    };

    connect();

    return () => {
      cancelled = true;
      clearTimers();
      clearPendingLocks("Conexão em tempo real encerrada.");
      const socket = socketRef.current;
      if (socket?.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: "presence.leave" }));
        socket.close();
      } else if (entityId && getAccessTokenRef.current?.()) {
        void clearCollaborationPresence(entityType, entityId, () => getAccessTokenRef.current?.());
      } else {
        socket?.close();
      }
      socketRef.current = null;
      setConnected(false);
    };
  }, [clearPendingLocks, enabled, entityId, entityType, sendMessage]);

  return {
    connected,
    connectionError,
    sendMessage,
    requestPresence,
    sendHeartbeat,
    acquireLock,
    releaseLock,
    leavePresence,
    clearPresence,
  };
}
