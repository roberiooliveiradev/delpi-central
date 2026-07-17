const STORAGE_KEY_PREFIX = "td-deck-editor-history:";
const STORAGE_VERSION = 2 as const;
export const DECK_EDITOR_HISTORY_POINTER_LIMIT = 500;

export type DeckEditorHistoryPointer = {
  snapshotId: string;
  revision: number;
};

export type DeckEditorHistoryStore = {
  version: typeof STORAGE_VERSION;
  updatedAt: number;
  past: DeckEditorHistoryPointer[];
  future: DeckEditorHistoryPointer[];
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

function normalizePointer(raw: unknown): DeckEditorHistoryPointer | null {
  if (!isRecord(raw)) return null;
  if (typeof raw.snapshotId !== "string" || !raw.snapshotId.trim()) return null;
  if (typeof raw.revision !== "number" || !Number.isFinite(raw.revision)) return null;
  return { snapshotId: raw.snapshotId, revision: raw.revision };
}

export function normalizeDeckEditorHistoryStore(raw: unknown): DeckEditorHistoryStore | null {
  if (!isRecord(raw)) return null;
  if (raw.version !== STORAGE_VERSION) return null;
  if (typeof raw.updatedAt !== "number" || !Number.isFinite(raw.updatedAt)) return null;
  if (!Array.isArray(raw.past) || !Array.isArray(raw.future)) return null;
  const past = raw.past
    .map(normalizePointer)
    .filter((item): item is DeckEditorHistoryPointer => item != null);
  const future = raw.future
    .map(normalizePointer)
    .filter((item): item is DeckEditorHistoryPointer => item != null);
  return {
    version: STORAGE_VERSION,
    updatedAt: raw.updatedAt,
    past: past.slice(-DECK_EDITOR_HISTORY_POINTER_LIMIT),
    future: future.slice(-DECK_EDITOR_HISTORY_POINTER_LIMIT),
  };
}

/** Cache leve: somente IDs/revisões; snapshots pertencem exclusivamente ao backend. */
export function readDeckEditorHistory(playlistId: string): DeckEditorHistoryStore | null {
  if (!canUseLocalStorage() || !playlistId.trim()) return null;
  try {
    const raw = window.localStorage.getItem(storageKey(playlistId));
    if (!raw) return null;
    const normalized = normalizeDeckEditorHistoryStore(JSON.parse(raw));
    if (!normalized) {
      window.localStorage.removeItem(storageKey(playlistId));
    }
    return normalized;
  } catch {
    return null;
  }
}

/** Grava ponteiros de undo/redo, nunca conteúdo da playlist. */
export function writeDeckEditorHistory(
  playlistId: string,
  past: readonly DeckEditorHistoryPointer[],
  future: readonly DeckEditorHistoryPointer[],
  updatedAt: number = Date.now(),
): void {
  if (!canUseLocalStorage() || !playlistId.trim()) return;
  try {
    const entry: DeckEditorHistoryStore = {
      version: STORAGE_VERSION,
      updatedAt,
      past: past.slice(-DECK_EDITOR_HISTORY_POINTER_LIMIT).map((item) => ({ ...item })),
      future: future.slice(-DECK_EDITOR_HISTORY_POINTER_LIMIT).map((item) => ({ ...item })),
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
