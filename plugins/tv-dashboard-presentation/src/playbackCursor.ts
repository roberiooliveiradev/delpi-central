/** Resolve índice do slide a partir do cursor compartilhado (modo reunião). */
export function applyPlaybackCursorToIndex(
  slides: ReadonlyArray<{ id: string }>,
  slideId: string,
  fallbackIndex?: number | null,
): number | null {
  if (!slides.length) return null;
  const byId = slides.findIndex((slide) => slide.id === slideId);
  if (byId >= 0) return byId;
  if (fallbackIndex == null || !Number.isFinite(fallbackIndex)) return null;
  const clamped = Math.max(0, Math.min(slides.length - 1, Math.floor(fallbackIndex)));
  return clamped;
}

const CLIENT_ID_PREFIX = "delpi-tv-playback-client:";

/** clientId estável por aba (sessionStorage) para ignorar eco do próprio cursor. */
export function resolvePresentationPlaybackClientId(scopeKey: string): string {
  const key = `${CLIENT_ID_PREFIX}${scopeKey || "default"}`;
  try {
    const existing = sessionStorage.getItem(key);
    if (existing && existing.trim()) return existing.trim();
    const id =
      typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
        ? crypto.randomUUID()
        : `tv-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
    sessionStorage.setItem(key, id);
    return id;
  } catch {
    return `tv-${Date.now().toString(36)}`;
  }
}
