/**
 * Foco de slide após `presentation_updated`.
 *
 * Causa raiz (ago/2026): todo evento com `slideId` (incl. autosave `slide_updated`
 * do peer) chamava `selectSlide` e roubava o slide ativo de quem editava outro slide.
 *
 * Só reasons de **criação** na playlist devem mudar a seleção local.
 */

/** Reasons da API/`notify_presentation_changed` que introduzem um slide a focar. */
export const PRESENTATION_SYNC_FOCUS_SLIDE_REASONS = Object.freeze(
  new Set([
    "slide_created",
    "slide_imported",
    "slide_duplicated",
    "copilot_blank_slide",
    "copilot_slide_from_preset",
  ]),
);

export type PresentationSyncFocusEvent = {
  reason?: string | null;
  slideId?: string | null;
};

/**
 * Retorna o `slideId` a focar no editor, ou `null` (reload sem trocar seleção).
 * Autosave, reorder, delete, patch de conteúdo e reconnect sem evento → `null`.
 */
export function resolvePresentationSyncFocusSlideId(
  event?: PresentationSyncFocusEvent | null,
  opts?: { currentSlideId?: string | null },
): string | null {
  if (!event) return null;
  const reason = String(event.reason ?? "").trim();
  const slideId = String(event.slideId ?? "").trim();
  if (!slideId || !PRESENTATION_SYNC_FOCUS_SLIDE_REASONS.has(reason)) {
    return null;
  }
  const current = String(opts?.currentSlideId ?? "").trim();
  if (current && current === slideId) return null;
  return slideId;
}
