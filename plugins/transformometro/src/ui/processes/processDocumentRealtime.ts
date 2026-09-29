/**
 * Pure decision layer for `entity.updated` events on the `processo:{id}` room.
 *
 * ProcessDocument writes (HTTP Portal + governed GPT/MCP) emit
 * `entityType: "process_document"` with `sectionKey: "documentacao"`. The WS
 * event is an invalidation signal only — the authoritative content is always
 * re-read from the HTTP API.
 */
import type { TransformometroEntityUpdatedEvent } from "../../constants/realtime";

export type ProcessDocumentRealtimeIntent =
  | { type: "ignore" }
  | { type: "refresh-list" }
  | { type: "refresh-list-and-detail" }
  | { type: "stale-draft" }
  | { type: "remote-delete"; editing: boolean };

export function documentIdFromEvent(
  event: TransformometroEntityUpdatedEvent,
): string | null {
  const payloadId = event.payload?.["document_id"];
  if (typeof payloadId === "string" && payloadId) return payloadId;
  return event.entityId || null;
}

/**
 * Decides what a `process_document` event means for the documentation UI.
 * Own-tab echoes (`actorClientId === clientId`) are ignored — the HTTP
 * response already refreshed the local state.
 */
export function resolveProcessDocumentEventIntent(
  event: TransformometroEntityUpdatedEvent,
  context: {
    selectedId: string | null;
    editingDocumentId: string | null;
    clientId: string;
  },
): ProcessDocumentRealtimeIntent {
  if (event.entityType !== "process_document") return { type: "ignore" };
  if (event.actorClientId && event.actorClientId === context.clientId) {
    return { type: "ignore" };
  }

  const documentId = documentIdFromEvent(event);
  const isEditingDoc =
    context.editingDocumentId != null && documentId === context.editingDocumentId;
  const isSelectedDoc =
    context.selectedId != null && documentId === context.selectedId;

  switch (event.action) {
    case "create":
      return { type: "refresh-list" };
    case "update":
      if (isEditingDoc) return { type: "stale-draft" };
      if (isSelectedDoc) return { type: "refresh-list-and-detail" };
      return { type: "refresh-list" };
    case "delete":
      if (isEditingDoc || isSelectedDoc) {
        return { type: "remote-delete", editing: isEditingDoc };
      }
      return { type: "refresh-list" };
    default:
      return isSelectedDoc && !context.editingDocumentId
        ? { type: "refresh-list-and-detail" }
        : { type: "refresh-list" };
  }
}
