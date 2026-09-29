/**
 * Pure decision layer for `entity.updated` events on the `revisao:{id}` room.
 *
 * Diagnostic writes emit `entityType: "diagnostic"` with
 * `sectionKey: "diagnostico"`; the payload is minimized (`revisao_id` only)
 * and is never a data source — the event is an invalidation signal and the
 * authoritative state is always re-read from the canonical GET endpoints.
 */
import type { TransformometroEntityUpdatedEvent } from "../../../constants/realtime";

export type DiagnosticRealtimeIntent =
  | { type: "ignore" }
  | { type: "refresh-list" }
  | { type: "refresh-list-and-detail" }
  | { type: "local-conflict" };

/**
 * Decides what a `diagnostic` event means for the section UI.
 *
 * Own-tab echoes (`actorClientId === clientId`) are ignored — the HTTP
 * response + canonical GET already refreshed local state.
 *
 * When the selected Diagnostic has local material state (open form or a
 * prepared proposal awaiting confirmation), a remote update must NOT
 * overwrite it: the UI surfaces a conflict banner instead (no auto-merge).
 */
export function resolveDiagnosticEventIntent(
  event: TransformometroEntityUpdatedEvent,
  context: {
    selectedId: string | null;
    hasLocalMaterialState: boolean;
    clientId: string;
  },
): DiagnosticRealtimeIntent {
  if (event.entityType !== "diagnostic") return { type: "ignore" };
  if (event.actorClientId && event.actorClientId === context.clientId) {
    return { type: "ignore" };
  }

  const isSelected =
    context.selectedId != null && event.entityId === context.selectedId;

  if (event.action === "create") return { type: "refresh-list" };
  if (isSelected) {
    return context.hasLocalMaterialState
      ? { type: "local-conflict" }
      : { type: "refresh-list-and-detail" };
  }
  return { type: "refresh-list" };
}
