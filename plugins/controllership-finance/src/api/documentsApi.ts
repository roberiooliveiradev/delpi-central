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
  httpPost,
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
  branch_scope: string;
  title: string | null;
  attachment_role: string;
  state: DocumentState;
  current_version_no: number;
  revision: number;
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

export type DocumentVersionState = "ATTACHED" | "SUPERSEDED";

export type DocumentVersion = {
  document_version_id: string;
  document_id: string;
  version_no: number;
  state: DocumentVersionState;
  uploaded_by: string;
  created_at: string | null;
  original_name: string;
  mime_type: string;
  size_bytes: number;
  checksum_sha256: string;
};

export type DocumentAuditEvent = {
  event_id: string;
  event_type: string;
  actor_subject: string;
  detail: Record<string, unknown>;
  created_at: string | null;
};

export type DocumentEventListResult = {
  events: DocumentAuditEvent[];
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
    branchScope?: "MATRIX" | "BRANCH" | "BOTH";
    limit?: number;
    offset?: number;
  } = {},
  options?: { signal?: AbortSignal },
): Promise<DocumentListResult> {
  const qs = buildQuery({
    snapshot_item_id: query.snapshotItemId ?? undefined,
    link_kind: query.linkKind,
    state: query.state,
    branch_scope: query.branchScope,
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
  options?: {
    signal?: AbortSignal;
    branchScope?: "MATRIX" | "BRANCH" | "BOTH";
  },
): Promise<Blob> {
  const qs = buildQuery({ branch_scope: options?.branchScope });
  return httpGetBlob(
    cfApiUrl(
      `/closing/competences/${period}/documents/${documentId}` +
        `/versions/${versionNo}/content${qs ? `?${qs}` : ""}`,
    ),
    { signal: options?.signal },
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

/** U5 — substitui o arquivo; a versão anterior fica SUPERSEDED. */
export async function replaceClosingDocument(
  period: string,
  documentId: string,
  input: { file: File; revision: number },
  options?: { signal?: AbortSignal; branchScope?: "MATRIX" | "BRANCH" | "BOTH" },
): Promise<ClosingDocument> {
  const formData = new FormData();
  formData.set("file", input.file);
  formData.set("revision", String(input.revision));
  if (options?.branchScope) {
    formData.set("branch_scope", options.branchScope);
  }
  const envelope = await httpPostFormData<Envelope<ClosingDocument>>(
    cfApiUrl(
      `/closing/competences/${period}/documents/${documentId}/versions`,
    ),
    formData,
    { signal: options?.signal },
  );
  if (!envelope?.data) {
    throw new Error("Resposta vazia ao substituir o documento.");
  }
  return envelope.data;
}

/** U6 — histórico imutável de versões (vN mais nova primeiro). */
export async function listDocumentVersions(
  period: string,
  documentId: string,
  options?: { signal?: AbortSignal; branchScope?: "MATRIX" | "BRANCH" | "BOTH" },
): Promise<DocumentVersion[]> {
  const qs = buildQuery({ branch_scope: options?.branchScope });
  const envelope = await httpGet<Envelope<{ versions: DocumentVersion[] }>>(
    cfApiUrl(
      `/closing/competences/${period}/documents/${documentId}/versions` +
        `${qs ? `?${qs}` : ""}`,
    ),
    { signal: options?.signal },
  );
  return envelope?.data?.versions ?? [];
}

/** U7 — cancelamento lógico; arquivos e histórico são preservados. */
export async function cancelClosingDocument(
  period: string,
  documentId: string,
  input: { revision: number },
  options?: { signal?: AbortSignal; branchScope?: "MATRIX" | "BRANCH" | "BOTH" },
): Promise<ClosingDocument> {
  const qs = buildQuery({ branch_scope: options?.branchScope });
  const envelope = await httpPost<Envelope<ClosingDocument>>(
    cfApiUrl(
      `/closing/competences/${period}/documents/${documentId}/cancel` +
        `${qs ? `?${qs}` : ""}`,
    ),
    { revision: input.revision },
    { signal: options?.signal },
  );
  if (!envelope?.data) {
    throw new Error("Resposta vazia ao cancelar o documento.");
  }
  return envelope.data;
}

/** U8 — eventos de auditoria do documento (mais recente primeiro). */
export async function listDocumentEvents(
  period: string,
  documentId: string,
  query: {
    branchScope?: "MATRIX" | "BRANCH" | "BOTH";
    limit?: number;
    offset?: number;
  } = {},
  options?: { signal?: AbortSignal },
): Promise<DocumentEventListResult> {
  const qs = buildQuery({
    branch_scope: query.branchScope,
    limit: query.limit !== undefined ? String(query.limit) : undefined,
    offset: query.offset !== undefined ? String(query.offset) : undefined,
  });
  const envelope = await httpGet<Envelope<DocumentEventListResult>>(
    cfApiUrl(
      `/closing/competences/${period}/documents/${documentId}/events` +
        `${qs ? `?${qs}` : ""}`,
    ),
    options,
  );
  return (
    envelope?.data ?? { events: [], total: 0, limit: 50, offset: 0 }
  );
}
