/**
 * Protocolo WS da sala de interação (subscribe / fan-out room.*).
 * Path do socket permanece `/commercial/realtime/ws` — só muda o payload.
 */

export type CommercialRoomMessageEvent = {
  type: "room.message.created" | "room.message.updated" | "room.message.deleted";
  roomId: string;
  messageId?: string;
  message?: Record<string, unknown> | null;
  actorUserId?: string | null;
  actorDisplayName?: string | null;
  actorClientId?: string | null;
};

export type CommercialRoomReactionEvent = {
  type: "room.reaction";
  roomId: string;
  messageId?: string;
  code?: string;
  action?: "set" | "clear" | string;
  userId?: string | null;
  actorUserId?: string | null;
  actorDisplayName?: string | null;
  actorClientId?: string | null;
};

export type CommercialRoomMentionEvent = {
  type: "room.mention";
  roomId: string;
  messageId?: string;
  mentionedUserIds?: string[];
  actorUserId?: string | null;
  actorDisplayName?: string | null;
  actorClientId?: string | null;
  notification?: {
    title?: string;
    message?: string;
    variant?: string;
  } | null;
};

export type CommercialRoomAttachmentEvent = {
  type: "room.attachment";
  reason?: string;
  roomId: string;
  messageId?: string;
  attachmentId?: string;
  fileName?: string | null;
  memberUserIds?: string[];
  actorUserId?: string | null;
  actorDisplayName?: string | null;
  notification?: {
    title?: string;
    message?: string;
    variant?: string;
  } | null;
};

export type CommercialRoomSubscribeAckEvent = {
  type: "subscribed" | "unsubscribed";
  roomId?: string;
  roomKey?: string;
};

export type CommercialRoomSubscribeErrorEvent = {
  type: "error";
  code?: string;
  roomId?: string;
  message?: string;
};

/** Eventos de negócio da sala (fan-out room:* ou user: mention/attachment). */
export type CommercialInteractionRoomEvent =
  | CommercialRoomMessageEvent
  | CommercialRoomReactionEvent
  | CommercialRoomMentionEvent
  | CommercialRoomAttachmentEvent;

const ROOM_FANOUT_TYPES = new Set([
  "room.message.created",
  "room.message.updated",
  "room.message.deleted",
  "room.reaction",
]);

const ROOM_USER_TYPES = new Set(["room.mention", "room.attachment"]);

export function isInteractionRoomFanoutType(type: string): boolean {
  return ROOM_FANOUT_TYPES.has(type);
}

export function isInteractionRoomUserType(type: string): boolean {
  return ROOM_USER_TYPES.has(type);
}

export function isInteractionRoomEventType(type: string): boolean {
  return isInteractionRoomFanoutType(type) || isInteractionRoomUserType(type);
}

export function buildInteractionRoomSubscribePayload(roomId: string): string {
  return JSON.stringify({ type: "subscribe", roomId: roomId.trim() });
}

export function buildInteractionRoomUnsubscribePayload(roomId: string): string {
  return JSON.stringify({ type: "unsubscribe", roomId: roomId.trim() });
}

export function interactionRoomEventTouchesRoom(
  event: { roomId?: string | null },
  roomId: string | null | undefined,
): boolean {
  const target = (roomId || "").trim();
  if (!target) return false;
  return (event.roomId || "").trim() === target;
}
