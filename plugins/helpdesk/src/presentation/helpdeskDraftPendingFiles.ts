/**
 * Pending inline images for create/reply drafts — File bytes in IndexedDB
 * (sessionStorage cannot hold File). Parity with interaction-room composer drafts.
 *
 * HTML draft keeps `data-attachment-pending` + stable `attachment:pending:{id}` src;
 * display blob: comes from resolve after hydrate.
 *
 * Writes are serialized per scope so an earlier paste snapshot cannot overwrite a
 * later rekey (pending uuid → document id) when arrayBuffer/put overlap (F5 H1).
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

/** Per-scope promise chain — shared so tests can assert serialization. */
const writeChainByScope = new Map<string, Promise<unknown>>();

/** @internal vitest — reset between cases. */
export function resetHelpdeskDraftWriteChainsForTests(): void {
  writeChainByScope.clear();
}

/**
 * Run async work for a draft scope strictly in enqueue order.
 * Earlier tasks finish before later ones start (stale paste cannot beat rekey).
 */
export function enqueueHelpdeskDraftScopeTask<T>(
  scope: string,
  task: () => Promise<T>,
  chains: Map<string, Promise<unknown>> = writeChainByScope,
): Promise<T> {
  const id = scope.trim();
  const prior = chains.get(id) ?? Promise.resolve();
  const run = prior.catch(() => undefined).then(() => task());
  chains.set(
    id,
    run.then(
      () => undefined,
      () => undefined,
    ),
  );
  return run;
}

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

/**
 * Keys that F5 hydrate must seed for a given draft HTML.
 * Used to detect IDB↔HTML mismatch (H3) without a browser.
 */
export function listDraftAttachmentSeedKeys(html: string): string[] {
  const keys: string[] = [];
  const seen = new Set<string>();
  const pendingRe = /data-attachment-pending=["']([^"']+)["']/gi;
  const idRe = /data-attachment-id=["'](\d+)["']/gi;
  let match: RegExpExecArray | null;
  while ((match = pendingRe.exec(String(html || "")))) {
    const id = match[1];
    if (!id || seen.has(id)) continue;
    seen.add(id);
    keys.push(id);
  }
  while ((match = idRe.exec(String(html || "")))) {
    const id = match[1];
    if (!id || seen.has(id)) continue;
    seen.add(id);
    keys.push(id);
  }
  return keys;
}

/**
 * True when every HTML attachment key has a File row to seed (F5 preview path).
 */
export function draftPendingFilesCoverHtml(
  html: string,
  rows: readonly HelpdeskDraftPendingFile[],
): boolean {
  const needed = listDraftAttachmentSeedKeys(html);
  if (needed.length === 0) return true;
  const have = new Set(rows.map((row) => row.id));
  return needed.every((id) => have.has(id));
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

async function writeHelpdeskDraftPendingFilesNow(
  scope: string,
  files: readonly HelpdeskDraftPendingFile[],
): Promise<void> {
  const db = await openDraftDb();
  const stored = await Promise.all(files.map(fileToStored));
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(HELPDESK_DRAFT_IDB_STORE, "readwrite");
    const store = tx.objectStore(HELPDESK_DRAFT_IDB_STORE);
    if (stored.length === 0) {
      store.delete(scope);
    } else {
      store.put(stored, scope);
    }
    tx.oncomplete = () => {
      db.close();
      resolve();
    };
    tx.onerror = () => reject(tx.error ?? new Error("idb put failed"));
  });
}

export async function writeHelpdeskDraftPendingFiles(
  scope: string,
  files: readonly HelpdeskDraftPendingFile[],
): Promise<void> {
  const id = scope.trim();
  if (!id) return;
  // Capture snapshot at enqueue time (caller already mapped from Map).
  const snapshot = files.map((item) => ({ id: item.id, file: item.file }));
  try {
    await enqueueHelpdeskDraftScopeTask(id, () =>
      writeHelpdeskDraftPendingFilesNow(id, snapshot),
    );
  } catch {
    /* best-effort — text draft still survives */
  }
}

export async function clearHelpdeskDraftPendingFiles(scope: string): Promise<void> {
  await writeHelpdeskDraftPendingFiles(scope, []);
}
