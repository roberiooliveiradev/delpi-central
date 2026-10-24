/** Cliente da BFF — evidências documentais do fechamento (P2-Upload SLICE-1).
 *
 * Contrato: `POST|GET /closing/competences/{period}/documents*` (doc 103).
 * `ATTACHED` é estado documental — nunca validação; o item do checklist
 * permanece `EXPECTED`. `idempotency_key` é obrigatória no corpo
 * multipart (D-U7=A) — gerada no cliente, nunca como header inventado.
 */
import {
  cfApiUrl,
  httpGet,
  httpGetBlob,
  httpPostFormData,
} from "./httpClient";

export type DocumentLinkKind = "competence" | "competence_item";
export type DocumentState = "ATTACHED" | "SUPERSEDED" | "CANCELLED";

export type ClosingDocument = {
  document_id: string;
  competence_id: string;
  link_kind: DocumentLinkKind;
  snapshot_item_id: string | null;
  snapshot_item_key: string | null;
  title: string | null;
  attachment_role: string;
  state: DocumentState;
  current_version_no: number;
  uploaded_by: string;
  created_at: string | null;
  updated_at: string | null;
  original_name: string | null;
  mime_type: string | null;
  size_bytes: number | null;
  checksum_sha256: string | null;
  deduplicated?: boolean;
};

export type DocumentListResult = {
  documents: ClosingDocument[];
  total: number;
  limit: number;
  offset: number;
};

type Envelope<T> = { success: boolean; data?: T | null };

export const CLOSING_DOCUMENT_MAX_BYTES = 25 * 1024 * 1024;
export const CLOSING_DOCUMENT_ACCEPT =
  ".pdf,.jpg,.jpeg,.png,.webp,.xls,.xlsx,.csv";

function buildQuery(params: Record<string, string | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") continue;
    search.set(key, value);
  }
  return search.toString();
}

/** U1 — upload de evidência (competência ou item do mesmo snapshot). */
export async function uploadClosingDocument(
  period: string,
  input: {
    file: File;
    idempotencyKey: string;
    snapshotItemId?: string | null;
    title?: string | null;
  },
  options?: { signal?: AbortSignal },
): Promise<ClosingDocument> {
  const formData = new FormData();
  formData.set("file", input.file);
  formData.set("idempotency_key", input.idempotencyKey);
  if (input.snapshotItemId) {
    formData.set("snapshot_item_id", input.snapshotItemId);
  }
  if (input.title) {
    formData.set("title", input.title);
  }
  const envelope = await httpPostFormData<Envelope<ClosingDocument>>(
    cfApiUrl(`/closing/competences/${period}/documents`),
    formData,
    options,
  );
  if (!envelope?.data) {
    throw new Error("Resposta vazia ao anexar o documento.");
  }
  return envelope.data;
}

/** U2 — listagem delimitada à competência do path. */
export async function listClosingDocuments(
  period: string,
  query: {
    snapshotItemId?: string | null;
    linkKind?: DocumentLinkKind;
    state?: DocumentState;
    limit?: number;
    offset?: number;
  } = {},
  options?: { signal?: AbortSignal },
): Promise<DocumentListResult> {
  const qs = buildQuery({
    snapshot_item_id: query.snapshotItemId ?? undefined,
    link_kind: query.linkKind,
    state: query.state,
    limit: query.limit !== undefined ? String(query.limit) : undefined,
    offset: query.offset !== undefined ? String(query.offset) : undefined,
  });
  const envelope = await httpGet<Envelope<DocumentListResult>>(
    cfApiUrl(
      `/closing/competences/${period}/documents${qs ? `?${qs}` : ""}`,
    ),
    options,
  );
  return (
    envelope?.data ?? { documents: [], total: 0, limit: 50, offset: 0 }
  );
}

/** U4 — download autenticado; bytes só chegam após autorização. */
export async function downloadClosingDocument(
  period: string,
  documentId: string,
  versionNo: number,
  options?: { signal?: AbortSignal },
): Promise<Blob> {
  return httpGetBlob(
    cfApiUrl(
      `/closing/competences/${period}/documents/${documentId}` +
        `/versions/${versionNo}/content`,
    ),
    options,
  );
}

/** Persiste o blob baixado com o nome original do servidor. */
export function saveDocumentBlob(blob: Blob, fileName: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
