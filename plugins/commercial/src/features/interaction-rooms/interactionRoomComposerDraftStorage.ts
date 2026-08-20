/**
 * Rascunho do composer da sala: texto em localStorage; anexos em IndexedDB
 * (File não serializa em localStorage). Chave por roomId.
 */

export const COMPOSER_DRAFT_TEXT_PREFIX =
  "commercial.interactionRoom.composerDraft.";
export const COMPOSER_DRAFT_IDB_NAME = "commercial-interaction-room-drafts";
export const COMPOSER_DRAFT_IDB_STORE = "pendingFiles";
export const COMPOSER_DRAFT_IDB_VERSION = 1;

export type ComposerDraftTextPayload = {
  bodyText: string;
  updatedAt: number;
};

export type ComposerDraftStoredFile = {
  id: string;
  name: string;
  type: string;
  lastModified: number;
  buffer: ArrayBuffer;
  /** clip = faixa de anexos; inline = colada no caret (`attachment:pending:`). */
  role: "clip" | "inline";
};

export type ComposerDraftPendingFile = {
  id: string;
  file: File;
  role: "clip" | "inline";
};

function textKey(roomId: string): string {
  return `${COMPOSER_DRAFT_TEXT_PREFIX}${roomId.trim()}`;
}

export function readComposerDraftText(roomId: string): string {
  const id = roomId.trim();
  if (!id || typeof window === "undefined") return "";
  try {
    const raw = window.localStorage.getItem(textKey(id));
    if (!raw) return "";
    const parsed = JSON.parse(raw) as ComposerDraftTextPayload;
    return typeof parsed.bodyText === "string" ? parsed.bodyText : "";
  } catch {
    return "";
  }
}

export function writeComposerDraftText(roomId: string, bodyText: string): void {
  const id = roomId.trim();
  if (!id || typeof window === "undefined") return;
  const trimmed = bodyText;
  if (!trimmed.trim()) {
    window.localStorage.removeItem(textKey(id));
    return;
  }
  const payload: ComposerDraftTextPayload = {
    bodyText: trimmed,
    updatedAt: Date.now(),
  };
  window.localStorage.setItem(textKey(id), JSON.stringify(payload));
}

export function clearComposerDraftText(roomId: string): void {
  const id = roomId.trim();
  if (!id || typeof window === "undefined") return;
  window.localStorage.removeItem(textKey(id));
}

function openDraftDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === "undefined") {
      reject(new Error("indexedDB unavailable"));
      return;
    }
    const request = indexedDB.open(COMPOSER_DRAFT_IDB_NAME, COMPOSER_DRAFT_IDB_VERSION);
    request.onerror = () => reject(request.error ?? new Error("indexedDB open failed"));
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(COMPOSER_DRAFT_IDB_STORE)) {
        db.createObjectStore(COMPOSER_DRAFT_IDB_STORE);
      }
    };
  });
}

async function fileToStored(
  item: ComposerDraftPendingFile,
): Promise<ComposerDraftStoredFile> {
  const buffer = await item.file.arrayBuffer();
  return {
    id: item.id,
    name: item.file.name,
    type: item.file.type,
    lastModified: item.file.lastModified,
    buffer,
    role: item.role === "inline" ? "inline" : "clip",
  };
}

function storedToFile(item: ComposerDraftStoredFile): ComposerDraftPendingFile {
  const file = new File([item.buffer], item.name, {
    type: item.type,
    lastModified: item.lastModified,
  });
  return {
    id: item.id,
    file,
    role: item.role === "inline" ? "inline" : "clip",
  };
}

export async function readComposerDraftFiles(
  roomId: string,
): Promise<ComposerDraftPendingFile[]> {
  const id = roomId.trim();
  if (!id) return [];
  try {
    const db = await openDraftDb();
    return await new Promise((resolve, reject) => {
      const tx = db.transaction(COMPOSER_DRAFT_IDB_STORE, "readonly");
      const store = tx.objectStore(COMPOSER_DRAFT_IDB_STORE);
      const request = store.get(id);
      request.onerror = () => reject(request.error ?? new Error("idb get failed"));
      request.onsuccess = () => {
        const rows = (request.result as ComposerDraftStoredFile[] | undefined) ?? [];
        resolve(Array.isArray(rows) ? rows.map(storedToFile) : []);
      };
      tx.oncomplete = () => db.close();
    });
  } catch {
    return [];
  }
}

export async function writeComposerDraftFiles(
  roomId: string,
  files: readonly ComposerDraftPendingFile[],
): Promise<void> {
  const id = roomId.trim();
  if (!id) return;
  try {
    const db = await openDraftDb();
    const stored = await Promise.all(files.map(fileToStored));
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(COMPOSER_DRAFT_IDB_STORE, "readwrite");
      const store = tx.objectStore(COMPOSER_DRAFT_IDB_STORE);
      if (stored.length === 0) {
        store.delete(id);
      } else {
        store.put(stored, id);
      }
      tx.oncomplete = () => {
        db.close();
        resolve();
      };
      tx.onerror = () => reject(tx.error ?? new Error("idb put failed"));
    });
  } catch {
    /* rascunho de anexos é best-effort */
  }
}

export async function clearComposerDraftFiles(roomId: string): Promise<void> {
  await writeComposerDraftFiles(roomId, []);
}

export async function clearComposerDraft(roomId: string): Promise<void> {
  clearComposerDraftText(roomId);
  await clearComposerDraftFiles(roomId);
}
