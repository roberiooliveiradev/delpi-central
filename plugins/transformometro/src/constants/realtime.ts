import type { CollaborationEntityType, CollaborationPresencePayload } from "../data/api/transformometroCollaborationApi";

/**
 * Broadcast invalidation can reference entities that are NOT collaboration
 * (presence/lock) entities — e.g. `process_document` events land on the
 * `processo:{id}` room. Presence/lock APIs stay bound to
 * `CollaborationEntityType`.
 */
export type RealtimeBroadcastEntityType =
  | CollaborationEntityType
  | "process_document"
  | (string & {});

export type TransformometroEntityUpdatedEvent = {
  type: "entity.updated";
  entityType: RealtimeBroadcastEntityType;
  entityId: string;
  action: string;
  sectionKey?: string | null;
  actorUserId?: string | null;
  /** Aba que originou a mutação HTTP (anti-eco). */
  actorClientId?: string | null;
  payload?: Record<string, unknown>;
};

export type TransformometroPresenceUpdatedEvent = {
  type: "presence.updated";
  entityType: CollaborationEntityType;
  entityId: string;
  data: CollaborationPresencePayload;
};

export type TransformometroLockResultEvent = {
  type: "lock.result";
  entityType: CollaborationEntityType;
  entityId: string;
  sectionKey?: string | null;
  data: {
    acquired?: boolean;
    holder?: CollaborationPresencePayload["editors"][number];
    presence?: CollaborationPresencePayload["editors"][number];
  };
};

export type TransformometroRealtimeErrorEvent = {
  type: "error";
  message: string;
  sectionKey?: string | null;
};

export type TransformometroRealtimeEvent =
  | TransformometroEntityUpdatedEvent
  | TransformometroPresenceUpdatedEvent
  | TransformometroLockResultEvent
  | TransformometroRealtimeErrorEvent
  | { type: "connected"; roomKey?: string; userId?: string; clientId?: string }
  | { type: "pong" };

export type TransformometroRealtimeOutbound =
  | { type: "presence.request" }
  | { type: "presence.heartbeat"; sectionKey?: string; mode: "viewing" | "editing" }
  | { type: "presence.leave" }
  | { type: "lock.acquire"; sectionKey: string }
  | { type: "lock.release"; sectionKey: string };

export function buildTransformometroRealtimeWsUrl(options: {
  entityType: CollaborationEntityType;
  entityId: string;
  token: string;
  clientId: string;
}): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const base =
    import.meta.env.VITE_TRANSFORMOMETRO_WS_BASE?.trim() ||
    `${protocol}//${window.location.host}/apps/transformometro-api/transformometro/realtime/ws`;

  const url = new URL(base, window.location.origin);
  url.searchParams.set("token", options.token);
  url.searchParams.set("entity_type", options.entityType);
  url.searchParams.set("entity_id", options.entityId);
  url.searchParams.set("client_id", options.clientId);
  return url.toString();
}
