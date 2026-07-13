const STORAGE_KEY_PREFIX = "td-deck-selected-slide:";

function canUseLocalStorage(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function storageKey(playlistId: string): string {
  return `${STORAGE_KEY_PREFIX}${playlistId}`;
}

/** Lê o slide selecionado persistido para a playlist (refresh / reabrir editor). */
export function readSelectedSlideId(playlistId: string): string | null {
  if (!canUseLocalStorage() || !playlistId.trim()) return null;
  try {
    const raw = window.localStorage.getItem(storageKey(playlistId));
    if (typeof raw !== "string" || !raw.trim()) return null;
    return raw.trim();
  } catch {
    return null;
  }
}

/** Grava o slide selecionado (ou limpa se `null`). */
export function writeSelectedSlideId(playlistId: string, slideId: string | null): void {
  if (!canUseLocalStorage() || !playlistId.trim()) return;
  try {
    const key = storageKey(playlistId);
    if (!slideId?.trim()) {
      window.localStorage.removeItem(key);
      return;
    }
    window.localStorage.setItem(key, slideId.trim());
  } catch {
    // quota / private mode
  }
}

/**
 * Escolhe o slide a restaurar: preferência salva se ainda existir na playlist;
 * senão o primeiro id disponível.
 */
export function resolveSelectedSlideId(
  playlistId: string,
  slideIds: readonly string[],
): string | null {
  if (!slideIds.length) return null;
  const saved = readSelectedSlideId(playlistId);
  if (saved && slideIds.includes(saved)) return saved;
  return slideIds[0] ?? null;
}
