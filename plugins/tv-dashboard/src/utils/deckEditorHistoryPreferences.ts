import type { DeckEditorSnapshot } from "./deckEditorHistory";
import { cloneDeckEditorSnapshot } from "./deckEditorHistory";

const STORAGE_KEY_PREFIX = "td-deck-editor-history:";
const STORAGE_VERSION = 1 as const;

export type DeckEditorHistoryStore = {
  version: typeof STORAGE_VERSION;
  updatedAt: number;
  past: DeckEditorSnapshot[];
  future: DeckEditorSnapshot[];
};

function canUseLocalStorage(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function storageKey(playlistId: string): string {
  return `${STORAGE_KEY_PREFIX}${playlistId}`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value != null && typeof value === "object" && !Array.isArray(value);
}

function normalizeSnapshot(raw: unknown): DeckEditorSnapshot | null {
  if (!isRecord(raw)) return null;
  if (!isRecord(raw.playlist)) return null;
  if (typeof raw.playlist.id !== "string" || !raw.playlist.id) return null;
  const selectedSlideId =
    raw.selectedSlideId == null
      ? null
      : typeof raw.selectedSlideId === "string"
        ? raw.selectedSlideId
        : null;
  try {
    return cloneDeckEditorSnapshot({
      selectedSlideId,
      playlist: raw.playlist as DeckEditorSnapshot["playlist"],
    });
  } catch {
    return null;
  }
}

export function normalizeDeckEditorHistoryStore(raw: unknown): DeckEditorHistoryStore | null {
  if (!isRecord(raw)) return null;
  if (raw.version !== STORAGE_VERSION) return null;
  if (typeof raw.updatedAt !== "number" || !Number.isFinite(raw.updatedAt)) return null;
  if (!Array.isArray(raw.past) || !Array.isArray(raw.future)) return null;
  const past = raw.past.map(normalizeSnapshot).filter((item): item is DeckEditorSnapshot => item != null);
  const future = raw.future
    .map(normalizeSnapshot)
    .filter((item): item is DeckEditorSnapshot => item != null);
  return {
    version: STORAGE_VERSION,
    updatedAt: raw.updatedAt,
    past,
    future,
  };
}

/** Lê a fila undo/redo persistida da playlist (sobrevive refresh). */
export function readDeckEditorHistory(playlistId: string): DeckEditorHistoryStore | null {
  if (!canUseLocalStorage() || !playlistId.trim()) return null;
  try {
    const raw = window.localStorage.getItem(storageKey(playlistId));
    if (!raw) return null;
    return normalizeDeckEditorHistoryStore(JSON.parse(raw));
  } catch {
    return null;
  }
}

/** Grava past/future no localStorage. */
export function writeDeckEditorHistory(
  playlistId: string,
  past: readonly DeckEditorSnapshot[],
  future: readonly DeckEditorSnapshot[],
  updatedAt: number = Date.now(),
): void {
  if (!canUseLocalStorage() || !playlistId.trim()) return;
  try {
    const entry: DeckEditorHistoryStore = {
      version: STORAGE_VERSION,
      updatedAt,
      past: past.map((item) => cloneDeckEditorSnapshot(item)),
      future: future.map((item) => cloneDeckEditorSnapshot(item)),
    };
    window.localStorage.setItem(storageKey(playlistId), JSON.stringify(entry));
  } catch {
    // quota / private mode
  }
}

export function clearDeckEditorHistory(playlistId: string): void {
  if (!canUseLocalStorage() || !playlistId.trim()) return;
  try {
    window.localStorage.removeItem(storageKey(playlistId));
  } catch {
    // ignore
  }
}
