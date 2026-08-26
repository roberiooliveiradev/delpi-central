import type { InteractionMessageDto, InteractionReactionDto } from "../api/interactionRoomsApi";
import type { CommercialInteractionRoomEvent } from "../constants/interactionRoomRealtime";

export type InteractionRoomThreadState = {
  messages: InteractionMessageDto[];
  pinnedMessageIds: Set<string>;
};

function textOrEmpty(value: unknown): string {
  return typeof value === "string" ? value : value == null ? "" : String(value);
}

function messageFromPayload(
  raw: Record<string, unknown> | null | undefined,
  fallbackId?: string,
): InteractionMessageDto | null {
  if (!raw || typeof raw !== "object") return null;
  const id = textOrEmpty(raw.id).trim() || (fallbackId || "").trim();
  if (!id) return null;
  const mentions = Array.isArray(raw.mentions) ? raw.mentions : [];
  const reactions = Array.isArray(raw.reactions) ? raw.reactions : [];
  return {
    id,
    room_id: textOrEmpty(raw.room_id),
    parent_id: raw.parent_id == null ? null : textOrEmpty(raw.parent_id),
    author_user_id:
      raw.author_user_id == null ? null : textOrEmpty(raw.author_user_id),
    message_kind: textOrEmpty(raw.message_kind) || "text",
    body_text: textOrEmpty(raw.body_text),
    edited_at: raw.edited_at == null ? null : textOrEmpty(raw.edited_at),
    deleted_at: raw.deleted_at == null ? null : textOrEmpty(raw.deleted_at),
    created_at: raw.created_at == null ? null : textOrEmpty(raw.created_at),
    mentions: mentions as InteractionMessageDto["mentions"],
    reactions: reactions as InteractionReactionDto[],
  };
}

function isOwnClient(
  event: { actorClientId?: string | null },
  ignoreActorClientId?: string | null,
): boolean {
  const actor = (event.actorClientId || "").trim();
  const self = (ignoreActorClientId || "").trim();
  return Boolean(actor && self && actor === self);
}

function upsertMessage(
  messages: InteractionMessageDto[],
  next: InteractionMessageDto,
): InteractionMessageDto[] {
  const index = messages.findIndex((item) => item.id === next.id);
  if (index < 0) return [...messages, next];
  const copy = messages.slice();
  copy[index] = { ...messages[index], ...next };
  return copy;
}

function applyReaction(
  messages: InteractionMessageDto[],
  messageId: string,
  userId: string,
  code: string,
  action: string,
): InteractionMessageDto[] {
  if (!messageId || !userId || !code) return messages;
  return messages.map((message) => {
    if (message.id !== messageId) return message;
    const current = [...(message.reactions ?? [])];
    if (action === "clear") {
      return {
        ...message,
        reactions: current.filter(
          (item) => !(item.user_id === userId && item.code === code),
        ),
      };
    }
    // set: uma reação por pessoa — remove todas do user e grava a nova.
    const withoutMine = current.filter((item) => item.user_id !== userId);
    withoutMine.push({ message_id: messageId, user_id: userId, code });
    return { ...message, reactions: withoutMine };
  });
}

/**
 * Aplica evento WS da sala no estado da thread (Page e Panel).
 * Inbox (`room.inbox.changed`) e toasts (`mention`/`attachment`) não alteram a lista.
 */
export function applyInteractionRoomRealtime(
  state: InteractionRoomThreadState,
  event: CommercialInteractionRoomEvent,
  options?: { ignoreActorClientId?: string | null },
): InteractionRoomThreadState {
  const ignore = options?.ignoreActorClientId;
  if (event.type === "room.inbox.changed") return state;
  if (event.type === "room.deleted") return state;
  if (event.type === "room.updated") return state;
  if (event.type === "room.mention") return state;
  if (event.type === "room.attachment") return state;

  if (event.type === "room.pin") {
    if (isOwnClient(event, ignore)) return state;
    const messageId = (event.messageId || "").trim();
    if (!messageId) return state;
    const next = new Set(state.pinnedMessageIds);
    if (event.action === "clear") next.delete(messageId);
    else next.add(messageId);
    return { ...state, pinnedMessageIds: next };
  }

  if (event.type === "room.reaction") {
    if (isOwnClient(event, ignore)) return state;
    const messageId = (event.messageId || "").trim();
    const userId = (event.userId || event.actorUserId || "").trim();
    const code = (event.code || "").trim();
    return {
      ...state,
      messages: applyReaction(
        state.messages,
        messageId,
        userId,
        code,
        event.action === "clear" ? "clear" : "set",
      ),
    };
  }

  if (event.type === "room.message.deleted") {
    if (isOwnClient(event, ignore)) return state;
    const messageId = (event.messageId || "").trim();
    if (!messageId) return state;
    const stamp =
      messageFromPayload(
        event.message as Record<string, unknown> | null,
        messageId,
      )?.deleted_at || new Date().toISOString();
    return {
      ...state,
      messages: state.messages.map((item) =>
        item.id === messageId ? { ...item, deleted_at: stamp } : item,
      ),
    };
  }

  if (
    event.type === "room.message.created" ||
    event.type === "room.message.updated"
  ) {
    if (isOwnClient(event, ignore)) return state;
    const mapped = messageFromPayload(
      event.message as Record<string, unknown> | null,
      event.messageId,
    );
    if (!mapped) return state;
    return { ...state, messages: upsertMessage(state.messages, mapped) };
  }

  return state;
}
