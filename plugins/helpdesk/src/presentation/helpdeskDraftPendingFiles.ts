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

/**
 * User intent for a staged file — independent from MIME type:
 *   inline     → image rendered inside the description html
 *   attachment → file staged as a removable ticket attachment
 * Legacy rows lack `kind`; restore falls back to the previous MIME heuristic.
 */
export type HelpdeskDraftPendingKind = "inline" | "attachment";

export type HelpdeskDraftStoredFile = {
  id: string;
  name: string;
  type: string;
  lastModified: number;
  buffer: ArrayBuffer;
  kind?: string;
};

export type HelpdeskDraftPendingFile = {
  id: string;
  file: File;
  kind?: HelpdeskDraftPendingKind;
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
    ...(item.kind ? { kind: item.kind } : null),
  };
}

function storedToFile(item: HelpdeskDraftStoredFile): HelpdeskDraftPendingFile {
  const file = new File([item.buffer], item.name, {
    type: item.type,
    lastModified: item.lastModified,
  });
  const kind =
    item.kind === "inline" || item.kind === "attachment" ? item.kind : undefined;
  return { id: item.id, file, ...(kind ? { kind } : null) };
}

export function replyDraftPendingScope(ticketId: string): string {
  return `reply:${String(ticketId).trim()}`;
}

/**
 * After upload, keep File bytes under the document id so F5 can re-seed
 * without waiting on GET /attachments (Bearer).
 *
 * Also keeps the pending uuid key (dual cover): if HTML rewrite races or
 * fails, F5 still resolves `data-attachment-pending` from the same File.
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
  if (!file) return;
  map.set(docKey, file);
  map.set(pendingKey, file);
}

/**
 * F5 preview path: only rewrite pending→document in HTML when IDB rows
 * already cover the post-rewrite keys (otherwise resolve stays null).
 */
export function canRewritePendingDraftHtml(
  rewrittenHtml: string,
  rows: readonly HelpdeskDraftPendingFile[],
): boolean {
  return draftPendingFilesCoverHtml(rewrittenHtml, rows);
}

/**
 * Restore-time kind resolution. Rows written before `kind` existed carry no
 * intent — fall back to the previous MIME heuristic so old drafts keep the
 * exact behavior they had (image rows stay out of the removable strip; the
 * editor restores their remove chrome instead of silently migrating them).
 */
export function resolveHelpdeskDraftPendingKind(
  row: HelpdeskDraftPendingFile,
  isInlineImage: (file: File) => boolean,
): HelpdeskDraftPendingKind {
  if (row.kind === "inline" || row.kind === "attachment") return row.kind;
  return isInlineImage(row.file) ? "inline" : "attachment";
}

/** Snapshot Map → IDB rows; `kinds` carries the per-id user intent. */
export function pendingFilesMapToDraftRows(
  map: Map<string, File>,
  kinds?: ReadonlyMap<string, HelpdeskDraftPendingKind>,
): HelpdeskDraftPendingFile[] {
  return [...map.entries()].map(([id, file]) => {
    const kind = kinds?.get(id);
    return kind ? { id, file, kind } : { id, file };
  });
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
  const snapshot = files.map((item) => ({
    id: item.id,
    file: item.file,
    ...(item.kind ? { kind: item.kind } : null),
  }));
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
