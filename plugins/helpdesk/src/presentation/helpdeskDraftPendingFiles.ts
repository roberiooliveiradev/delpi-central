/**
 * Pending inline images for create/reply drafts — File bytes in IndexedDB
 * (sessionStorage cannot hold File). Parity with interaction-room composer drafts.
 *
 * HTML draft keeps `data-attachment-pending` + stable `attachment:pending:{id}` src;
 * display blob: comes from resolve after hydrate.
 */

export const HELPDESK_DRAFT_IDB_NAME = "helpdesk-ticket-drafts";
export const HELPDESK_DRAFT_IDB_STORE = "pendingFiles";
export const HELPDESK_DRAFT_IDB_VERSION = 1;

/** Stable draft scope keys. */
export const HELPDESK_CREATE_DRAFT_SCOPE = "create";

export type HelpdeskDraftStoredFile = {
  id: string;
  name: string;
  type: string;
  lastModified: number;
  buffer: ArrayBuffer;
};

export type HelpdeskDraftPendingFile = {
  id: string;
  file: File;
};

function openDraftDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === "undefined") {
      reject(new Error("indexedDB unavailable"));
      return;
    }
    const request = indexedDB.open(HELPDESK_DRAFT_IDB_NAME, HELPDESK_DRAFT_IDB_VERSION);
    request.onerror = () => reject(request.error ?? new Error("indexedDB open failed"));
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(HELPDESK_DRAFT_IDB_STORE)) {
        db.createObjectStore(HELPDESK_DRAFT_IDB_STORE);
      }
    };
  });
}

async function fileToStored(item: HelpdeskDraftPendingFile): Promise<HelpdeskDraftStoredFile> {
  const buffer = await item.file.arrayBuffer();
  return {
    id: item.id,
    name: item.file.name,
    type: item.file.type,
    lastModified: item.file.lastModified,
    buffer,
  };
}

function storedToFile(item: HelpdeskDraftStoredFile): HelpdeskDraftPendingFile {
  const file = new File([item.buffer], item.name, {
    type: item.type,
    lastModified: item.lastModified,
  });
  return { id: item.id, file };
}

export function replyDraftPendingScope(ticketId: string): string {
  return `reply:${String(ticketId).trim()}`;
}

/**
 * After upload rewrite, keep File bytes under the document id so F5 can
 * re-seed the blob without waiting on GET /attachments (Bearer).
 */
export function rekeyDraftFileToDocument(
  map: Map<string, File>,
  pendingId: string,
  documentId: number | string,
): void {
  const pendingKey = String(pendingId || "").trim();
  const docKey = String(documentId);
  if (!pendingKey || !docKey) return;
  const file = map.get(pendingKey);
  map.delete(pendingKey);
  if (file) map.set(docKey, file);
}

/** Snapshot Map → IDB rows (inline pending images only). */
export function pendingFilesMapToDraftRows(
  map: Map<string, File>,
): HelpdeskDraftPendingFile[] {
  return [...map.entries()].map(([id, file]) => ({ id, file }));
}

export async function readHelpdeskDraftPendingFiles(
  scope: string,
): Promise<HelpdeskDraftPendingFile[]> {
  const id = scope.trim();
  if (!id) return [];
  try {
    const db = await openDraftDb();
    return await new Promise((resolve, reject) => {
      const tx = db.transaction(HELPDESK_DRAFT_IDB_STORE, "readonly");
      const store = tx.objectStore(HELPDESK_DRAFT_IDB_STORE);
      const request = store.get(id);
      request.onerror = () => reject(request.error ?? new Error("idb get failed"));
      request.onsuccess = () => {
        const rows = (request.result as HelpdeskDraftStoredFile[] | undefined) ?? [];
        resolve(Array.isArray(rows) ? rows.map(storedToFile) : []);
      };
      tx.oncomplete = () => db.close();
    });
  } catch {
    return [];
  }
}

export async function writeHelpdeskDraftPendingFiles(
  scope: string,
  files: readonly HelpdeskDraftPendingFile[],
): Promise<void> {
  const id = scope.trim();
  if (!id) return;
  try {
    const db = await openDraftDb();
    const stored = await Promise.all(files.map(fileToStored));
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(HELPDESK_DRAFT_IDB_STORE, "readwrite");
      const store = tx.objectStore(HELPDESK_DRAFT_IDB_STORE);
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
    /* best-effort — text draft still survives */
  }
}

export async function clearHelpdeskDraftPendingFiles(scope: string): Promise<void> {
  await writeHelpdeskDraftPendingFiles(scope, []);
}
