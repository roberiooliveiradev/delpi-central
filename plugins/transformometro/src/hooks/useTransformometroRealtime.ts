import { useEffect, useRef, useState } from "react";

import type { CollaborationEntityType, CollaborationPresencePayload } from "../data/api/transformometroCollaborationApi";
import {
  buildTransformometroRealtimeWsUrl,
  type TransformometroEntityUpdatedEvent,
} from "../constants/realtime";
import { getTransformometroClientId } from "../utils/clientId";

const PING_MS = 25_000;
const RECONNECT_MS = 4_000;

type Options = {
  entityType: CollaborationEntityType;
  entityId: string;
  getAccessToken?: () => string | undefined;
  enabled?: boolean;
  onPresenceUpdated?: (presence: CollaborationPresencePayload) => void;
  onEntityUpdated?: (event: TransformometroEntityUpdatedEvent) => void;
};

export function useTransformometroRealtime({
  entityType,
  entityId,
  getAccessToken,
  enabled = true,
  onPresenceUpdated,
  onEntityUpdated,
}: Options) {
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const pingTimerRef = useRef<number | null>(null);
  const clientIdRef = useRef(getTransformometroClientId());

  const onPresenceUpdatedRef = useRef(onPresenceUpdated);
  const onEntityUpdatedRef = useRef(onEntityUpdated);
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
    getAccessTokenRef.current = getAccessToken;
  }, [getAccessToken]);

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
        pingTimerRef.current = window.setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) {
            socket.send("ping");
          }
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
            payload?: Record<string, unknown>;
          };

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
  }, [enabled, entityId, entityType]);

  return { connected, connectionError };
}
