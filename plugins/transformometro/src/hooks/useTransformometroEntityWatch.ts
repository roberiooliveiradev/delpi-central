import { useEffect, useRef } from "react";

import type { CollaborationEntityType } from "../data/api/transformometroCollaborationApi";
import {
  buildTransformometroRealtimeWsUrl,
  type TransformometroEntityUpdatedEvent,
} from "../constants/realtime";
import { getTransformometroClientId } from "../utils/clientId";

const PING_MS = 25_000;
const RECONNECT_MS = 4_000;

type WatchedEntity = {
  entityType: CollaborationEntityType;
  entityId: string;
};

type Options = {
  entities: WatchedEntity[];
  getAccessToken?: () => string | undefined;
  enabled?: boolean;
  onEntityUpdated?: (event: TransformometroEntityUpdatedEvent) => void;
};

function entitiesKey(entities: WatchedEntity[]): string {
  return entities
    .filter((item) => item.entityId)
    .map((item) => `${item.entityType}:${item.entityId}`)
    .sort()
    .join("|");
}

export function useTransformometroEntityWatch({
  entities,
  getAccessToken,
  enabled = true,
  onEntityUpdated,
}: Options) {
  const onEntityUpdatedRef = useRef(onEntityUpdated);
  const getAccessTokenRef = useRef(getAccessToken);
  const clientIdRef = useRef(getTransformometroClientId());

  useEffect(() => {
    onEntityUpdatedRef.current = onEntityUpdated;
  }, [onEntityUpdated]);

  useEffect(() => {
    getAccessTokenRef.current = getAccessToken;
  }, [getAccessToken]);

  useEffect(() => {
    const watched = entities.filter((item) => item.entityId);
    if (!enabled || watched.length === 0) {
      return;
    }

    let cancelled = false;
    const sockets = new Map<string, WebSocket>();
    const reconnectTimers = new Map<string, number>();
    const pingTimers = new Map<string, number>();

    const clearSocketTimers = (key: string) => {
      const reconnect = reconnectTimers.get(key);
      if (reconnect != null) {
        window.clearTimeout(reconnect);
        reconnectTimers.delete(key);
      }
      const ping = pingTimers.get(key);
      if (ping != null) {
        window.clearInterval(ping);
        pingTimers.delete(key);
      }
    };

    const connectEntity = (entity: WatchedEntity) => {
      const key = `${entity.entityType}:${entity.entityId}`;
      clearSocketTimers(key);
      sockets.get(key)?.close();
      sockets.delete(key);

      const token = getAccessTokenRef.current?.();
      if (!token) {
        if (cancelled || reconnectTimers.has(key)) return;
        reconnectTimers.set(
          key,
          window.setTimeout(() => connectEntity(entity), RECONNECT_MS)
        );
        return;
      }

      let socket: WebSocket;
      try {
        socket = new WebSocket(
          buildTransformometroRealtimeWsUrl({
            entityType: entity.entityType,
            entityId: entity.entityId,
            token,
            clientId: clientIdRef.current,
          })
        );
      } catch {
        if (cancelled || reconnectTimers.has(key)) return;
        reconnectTimers.set(
          key,
          window.setTimeout(() => connectEntity(entity), RECONNECT_MS)
        );
        return;
      }

      sockets.set(key, socket);

      socket.onopen = () => {
        if (cancelled) return;
        pingTimers.set(
          key,
          window.setInterval(() => {
            if (socket.readyState === WebSocket.OPEN) {
              socket.send("ping");
            }
          }, PING_MS)
        );
      };

      socket.onmessage = (event) => {
        if (cancelled) return;
        try {
          const payload = JSON.parse(String(event.data)) as {
            type?: string;
            entityType?: CollaborationEntityType;
            entityId?: string;
            action?: string;
            sectionKey?: string | null;
            actorUserId?: string | null;
            payload?: Record<string, unknown>;
          };

          if (payload.type !== "entity.updated" || !payload.entityType || !payload.entityId) {
            return;
          }

          onEntityUpdatedRef.current?.({
            type: "entity.updated",
            entityType: payload.entityType,
            entityId: payload.entityId,
            action: payload.action ?? "updated",
            sectionKey: payload.sectionKey,
            actorUserId: payload.actorUserId,
            payload: payload.payload,
          });
        } catch {
          /* ignore malformed payloads */
        }
      };

      socket.onclose = () => {
        clearSocketTimers(key);
        sockets.delete(key);
        if (cancelled || reconnectTimers.has(key)) return;
        reconnectTimers.set(
          key,
          window.setTimeout(() => connectEntity(entity), RECONNECT_MS)
        );
      };
    };

    for (const entity of watched) {
      connectEntity(entity);
    }

    return () => {
      cancelled = true;
      for (const key of reconnectTimers.keys()) {
        clearSocketTimers(key);
      }
      for (const socket of sockets.values()) {
        socket.close();
      }
      sockets.clear();
    };
  }, [enabled, entitiesKey(entities)]);
}
