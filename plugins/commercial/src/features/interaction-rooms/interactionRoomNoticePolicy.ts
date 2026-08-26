import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";

export type InteractionRoomNoticeSurface = "floating" | "banner";

export type InteractionRoomComposerNoticeKind =
  | "success"
  | "info"
  | "warning"
  | "error";

/** Feedback imediato de ações locais (enviar, pin, tarefa, erro de composer). */
export function interactionRoomComposerNoticeSurface(): InteractionRoomNoticeSurface {
  return "floating";
}

/** Erros bloqueantes de fetch ou WS caem no banner do workspace/thread. */
export function interactionRoomBlockingNoticeSurface(): InteractionRoomNoticeSurface {
  return "banner";
}

/** Eventos de terceiros na thread usam toast flutuante (não AlertQueue). */
export function interactionRoomThirdPartyRealtimeNoticeSurface(): InteractionRoomNoticeSurface {
  return "floating";
}

export function interactionRoomNoticeVariantForComposerKind(
  kind: InteractionRoomComposerNoticeKind,
): "success" | "info" | "warning" | "error" {
  return kind;
}

export function isInteractionRoomOwnActor(
  actorClientId: string | null | undefined,
  selfClientId: string | null | undefined,
): boolean {
  const actor = (actorClientId ?? "").trim();
  const self = (selfClientId ?? "").trim();
  return Boolean(actor && self && actor === self);
}

export function formatInteractionRoomPinByOtherNotice(authorLabel: string): string {
  const label = authorLabel.trim() || INTERACTION_ROOMS_CONTENT.roomFallbackAuthor;
  return INTERACTION_ROOMS_CONTENT.noticePinByOtherTemplate.replace(
    "{author}",
    label,
  );
}

export function formatInteractionRoomReactionByOtherNotice(
  authorLabel: string,
  emoji: string,
): string {
  const label = authorLabel.trim() || INTERACTION_ROOMS_CONTENT.roomFallbackAuthor;
  const symbol = emoji.trim() || INTERACTION_ROOMS_CONTENT.noticeReactionFallbackEmoji;
  return INTERACTION_ROOMS_CONTENT.noticeReactionByOtherTemplate
    .replace("{author}", label)
    .replace("{emoji}", symbol);
}
