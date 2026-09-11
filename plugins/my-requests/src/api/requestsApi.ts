import { httpDelete, httpGet, httpPatch, httpPost, getAccessToken, DELPI_CALLER_APP } from "./httpClient";
import {
  getMyRequestsClientId,
  MY_REQUESTS_CLIENT_ID_HEADER,
} from "../app/myRequestsClientId";
import type {
  Envelope,
  RequestArtifact,
  RequestAttachment,
  RequestComment,
  RequestDetail,
  RequestListResponse,
  RequestTypeSummary,
  TimelineEvent,
} from "../types/requests";

export const API_BASE = "/apps/requests-api/v1";

function clientHeaders(): Record<string, string> {
  return {
    "X-Delpi-Caller-App": DELPI_CALLER_APP,
    [MY_REQUESTS_CLIENT_ID_HEADER]: getMyRequestsClientId(),
    ...(getAccessToken() ? { Authorization: `Bearer ${getAccessToken()}` } : {}),
  };
}

export type RequestListQuery = {
  signal?: AbortSignal;
  page?: number;
  pageSize?: number;
  typeCode?: string;
  status?: string;
  branch?: string;
  q?: string;
  mineScope?: "completed_by_me" | "assigned_to_me";
};

export function buildRequestListQueryParams(options?: RequestListQuery): string {
  const params = new URLSearchParams();
  if (options?.page) params.set("page", String(options.page));
  if (options?.pageSize) params.set("page_size", String(options.pageSize));
  const typeCode = options?.typeCode?.trim();
  if (typeCode) params.set("type_code", typeCode);
  const status = options?.status?.trim();
  if (status) params.set("status", status);
  const branch = options?.branch?.trim();
  if (branch) params.set("branch", branch);
  const q = options?.q?.trim();
  if (q && q.length >= 2) params.set("q", q);
  const mineScope = options?.mineScope?.trim();
  if (mineScope) params.set("mine_scope", mineScope);
  return params.toString();
}

export function unwrapEnvelope<T>(body: Envelope<T>): T {
  if (!body.success) {
    throw new Error(body.message || "Erro na API de Minhas Solicitações.");
  }
  return body.data;
}

function unwrap<T>(body: Envelope<T>): T {
  return unwrapEnvelope(body);
}

export async function listRequestTypes(options?: { signal?: AbortSignal }) {
  const body = await httpGet<Envelope<{ items: RequestTypeSummary[] } | RequestTypeSummary[]>>(
    `${API_BASE}/request-types`,
    options,
  );
  const data = unwrap(body);
  if (Array.isArray(data)) return data;
  return data.items || [];
}

export async function listMyRequests(options?: RequestListQuery) {
  const qs = buildRequestListQueryParams(options);
  const body = await httpGet<Envelope<RequestListResponse>>(
    `${API_BASE}/requests/mine${qs ? `?${qs}` : ""}`,
    options,
  );
  return unwrap(body);
}

export async function listWorkQueue(options?: RequestListQuery) {
  const qs = buildRequestListQueryParams(options);
  const body = await httpGet<Envelope<RequestListResponse>>(
    `${API_BASE}/requests/work-queue${qs ? `?${qs}` : ""}`,
    options,
  );
  return unwrap(body);
}

export async function getRequest(requestId: string, options?: { signal?: AbortSignal }) {
  const body = await httpGet<Envelope<RequestDetail>>(
    `${API_BASE}/requests/${encodeURIComponent(requestId)}`,
    options,
  );
  return unwrap(body);
}

export async function createRequest(input: {
  typeCode: string;
  branchCode?: string;
  priority?: string;
  payload?: Record<string, unknown>;
  idempotencyKey: string;
}) {
  const response = await fetch(`${API_BASE}/requests`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      "Idempotency-Key": input.idempotencyKey,
      ...clientHeaders(),
    },
    body: JSON.stringify({
      type_code: input.typeCode,
      branch: input.branchCode,
      priority: input.priority || "normal",
      payload: input.payload || {},
    }),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Erro HTTP ${response.status}`);
  }
  const body = (await response.json()) as Envelope<RequestDetail>;
  return unwrap(body);
}

export async function transitionRequest(
  requestId: string,
  action: string,
  input: {
    version?: number;
    returnReason?: string;
    cancelJustification?: string;
    correctionTargets?: string[];
    idempotencyKey: string;
  },
) {
  const response = await fetch(
    `${API_BASE}/requests/${encodeURIComponent(requestId)}/transitions/${encodeURIComponent(action)}`,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "Idempotency-Key": input.idempotencyKey,
        ...clientHeaders(),
      },
      body: JSON.stringify({
        version: input.version,
        return_reason: input.returnReason,
        cancel_justification: input.cancelJustification,
        correction_targets: input.correctionTargets,
      }),
    },
  );
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Erro HTTP ${response.status}`);
  }
  const body = (await response.json()) as Envelope<RequestDetail>;
  return unwrap(body);
}

export async function patchRequestPayload(
  requestId: string,
  payload: Record<string, unknown>,
  input: { version?: number; idempotencyKey: string },
) {
  const response = await fetch(`${API_BASE}/requests/${encodeURIComponent(requestId)}`, {
    method: "PATCH",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      "Idempotency-Key": input.idempotencyKey,
      ...clientHeaders(),
    },
    body: JSON.stringify({
      payload,
      version: input.version,
    }),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Erro HTTP ${response.status}`);
  }
  const body = (await response.json()) as Envelope<RequestDetail>;
  return unwrap(body);
}

export async function listEvents(requestId: string, options?: { signal?: AbortSignal }) {
  const body = await httpGet<Envelope<{ items: TimelineEvent[]; total: number }>>(
    `${API_BASE}/requests/${encodeURIComponent(requestId)}/events`,
    options,
  );
  return unwrap(body);
}

export async function listComments(requestId: string, options?: { signal?: AbortSignal }) {
  const body = await httpGet<Envelope<{ items: RequestComment[]; total: number }>>(
    `${API_BASE}/requests/${encodeURIComponent(requestId)}/comments`,
    options,
  );
  return unwrap(body);
}

export async function createComment(requestId: string, text: string) {
  return unwrap(
    await httpPost<Envelope<RequestComment>>(
      `${API_BASE}/requests/${encodeURIComponent(requestId)}/comments`,
      { body: text },
    ),
  );
}

export async function patchComment(
  requestId: string,
  commentId: string,
  text: string,
  options?: { markAsEdited?: boolean },
) {
  return unwrap(
    await httpPatch<Envelope<RequestComment>>(
      `${API_BASE}/requests/${encodeURIComponent(requestId)}/comments/${encodeURIComponent(commentId)}`,
      {
        body: text,
        mark_as_edited: options?.markAsEdited ?? true,
      },
    ),
  );
}

export type CommentAttachmentMeta = {
  id: string;
  comment_id: string;
  original_name: string;
  mime_type: string | null;
  size_bytes: number | null;
};

export async function listCommentAttachments(
  requestId: string,
  commentId: string,
  options?: { signal?: AbortSignal },
): Promise<CommentAttachmentMeta[]> {
  const body = await httpGet<
    Envelope<{ items: Array<Record<string, unknown>> }>
  >(
    `${API_BASE}/requests/${encodeURIComponent(requestId)}/comments/${encodeURIComponent(commentId)}/attachments`,
    options,
  );
  const items = unwrap(body).items || [];
  return items.map((row) => ({
    id: String(row.id ?? ""),
    comment_id: String(row.comment_id ?? commentId),
    original_name: String(row.original_name || "imagem"),
    mime_type: (row.mime_type as string | null | undefined) ?? null,
    size_bytes: (row.size_bytes as number | null | undefined) ?? null,
  }));
}

export async function uploadCommentAttachment(
  requestId: string,
  commentId: string,
  file: File,
): Promise<CommentAttachmentMeta> {
  const form = new FormData();
  form.append("file", file, file.name);
  const response = await fetch(
    `${API_BASE}/requests/${encodeURIComponent(requestId)}/comments/${encodeURIComponent(commentId)}/attachments`,
    {
      method: "POST",
      headers: clientHeaders(),
      body: form,
    },
  );
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Erro HTTP ${response.status}`);
  }
  const body = (await response.json()) as Envelope<Record<string, unknown>>;
  const row = unwrap(body);
  return {
    id: String(row.id ?? ""),
    comment_id: String(row.comment_id ?? commentId),
    original_name: String(row.original_name || file.name),
    mime_type: (row.mime_type as string | null | undefined) ?? (file.type || null),
    size_bytes: (row.size_bytes as number | null | undefined) ?? file.size,
  };
}

export async function deleteCommentAttachment(
  requestId: string,
  commentId: string,
  attachmentId: string,
): Promise<void> {
  await httpDelete(
    `${API_BASE}/requests/${encodeURIComponent(requestId)}` +
      `/comments/${encodeURIComponent(commentId)}` +
      `/attachments/${encodeURIComponent(attachmentId)}`,
  );
}

export function commentAttachmentContentUrl(
  requestId: string,
  commentId: string,
  attachmentId: string,
) {
  return (
    `${API_BASE}/requests/${encodeURIComponent(requestId)}` +
    `/comments/${encodeURIComponent(commentId)}` +
    `/attachments/${encodeURIComponent(attachmentId)}/content`
  );
}

export async function downloadCommentAttachmentBlob(
  requestId: string,
  commentId: string,
  attachmentId: string,
  options?: { signal?: AbortSignal },
): Promise<Blob> {
  const response = await fetch(
    commentAttachmentContentUrl(requestId, commentId, attachmentId),
    {
      method: "GET",
      headers: clientHeaders(),
      signal: options?.signal,
    },
  );
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Erro HTTP ${response.status}`);
  }
  return response.blob();
}

export async function listAttachments(requestId: string, options?: { signal?: AbortSignal }) {
  const body = await httpGet<Envelope<{ items: RequestAttachment[]; total?: number } | RequestAttachment[]>>(
    `${API_BASE}/requests/${encodeURIComponent(requestId)}/attachments`,
    options,
  );
  const data = unwrap(body);
  const items = Array.isArray(data) ? data : data.items || [];
  return items.map(normalizeAttachment);
}

function normalizeAttachment(raw: Record<string, unknown> | RequestAttachment): RequestAttachment {
  const row = raw as Record<string, unknown>;
  return {
    id: String(row.id ?? ""),
    file_name: String(row.file_name || row.original_name || "anexo"),
    content_type: (row.content_type as string | null | undefined) ?? (row.mime_type as string | null | undefined) ?? null,
    size_bytes: (row.size_bytes as number | null | undefined) ?? null,
    created_at: (row.created_at as string | null | undefined) ?? null,
  };
}

export async function uploadAttachment(requestId: string, file: File, idempotencyKey?: string) {
  const form = new FormData();
  form.append("file", file, file.name);
  const response = await fetch(
    `${API_BASE}/requests/${encodeURIComponent(requestId)}/attachments`,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        ...(idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {}),
        ...clientHeaders(),
      },
      body: form,
    },
  );
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Erro HTTP ${response.status}`);
  }
  const body = (await response.json()) as Envelope<Record<string, unknown>>;
  return normalizeAttachment(unwrap(body));
}

export async function deleteAttachment(attachmentId: string) {
  return unwrap(
    await httpDelete<Envelope<{ id: string; deleted: boolean }>>(
      `${API_BASE}/attachments/${encodeURIComponent(attachmentId)}`,
    ),
  );
}

export async function deleteArtifact(artifactId: string) {
  return unwrap(
    await httpDelete<Envelope<{ id: string; deleted: boolean }>>(
      `${API_BASE}/artifacts/${encodeURIComponent(artifactId)}`,
    ),
  );
}

/** Authenticated blob fetch for image thumbnails (download endpoint). */
export async function downloadAttachmentBlob(attachmentId: string): Promise<Blob> {
  const response = await fetch(attachmentDownloadUrl(attachmentId), {
    method: "GET",
    headers: clientHeaders(),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Erro HTTP ${response.status}`);
  }
  return response.blob();
}

export async function downloadArtifactBlob(artifactId: string): Promise<Blob> {
  const response = await fetch(artifactDownloadUrl(artifactId), {
    method: "GET",
    headers: clientHeaders(),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Erro HTTP ${response.status}`);
  }
  return response.blob();
}

export async function listArtifacts(requestId: string, options?: { signal?: AbortSignal }) {
  const body = await httpGet<Envelope<{ items: RequestArtifact[]; total?: number } | RequestArtifact[]>>(
    `${API_BASE}/requests/${encodeURIComponent(requestId)}/artifacts`,
    options,
  );
  const data = unwrap(body);
  const items = Array.isArray(data) ? data : data.items || [];
  return items.map(normalizeArtifact);
}

function normalizeArtifact(raw: Record<string, unknown> | RequestArtifact): RequestArtifact {
  const row = raw as Record<string, unknown>;
  return {
    id: String(row.id ?? ""),
    file_name: String(row.file_name || row.original_name || "artefato"),
    content_type:
      (row.content_type as string | null | undefined) ??
      (row.mime_type as string | null | undefined) ??
      null,
    size_bytes: (row.size_bytes as number | null | undefined) ?? null,
    kind:
      (row.kind as string | null | undefined) ??
      (row.artifact_kind as string | null | undefined) ??
      null,
    created_at: (row.created_at as string | null | undefined) ?? null,
  };
}

export type UploadArtifactOptions = {
  artifactKind?: string;
  idempotencyKey?: string;
};

export async function uploadArtifact(
  requestId: string,
  file: File,
  options?: UploadArtifactOptions,
) {
  const form = new FormData();
  form.append("file", file, file.name);
  form.append("artifact_kind", (options?.artifactKind || "generic").trim() || "generic");
  const idempotencyKey = options?.idempotencyKey;
  const response = await fetch(
    `${API_BASE}/requests/${encodeURIComponent(requestId)}/artifacts`,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        ...(idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {}),
        ...clientHeaders(),
      },
      body: form,
    },
  );
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Erro HTTP ${response.status}`);
  }
  const body = (await response.json()) as Envelope<Record<string, unknown>>;
  return normalizeArtifact(unwrap(body));
}

export function attachmentDownloadUrl(attachmentId: string) {
  return `${API_BASE}/attachments/${encodeURIComponent(attachmentId)}/download`;
}

export function artifactDownloadUrl(artifactId: string) {
  return `${API_BASE}/artifacts/${encodeURIComponent(artifactId)}/download`;
}

export function participantAvatarUrl(userId: string) {
  return `${API_BASE}/participants/${encodeURIComponent(userId)}/avatar`;
}

export async function lookupParticipantsHasPhoto(
  userIds: string[],
  options?: { signal?: AbortSignal },
): Promise<Array<{ user_id: string; has_photo: boolean }>> {
  const body = await httpPost<
    Envelope<{ items: Array<{ user_id: string; has_photo: boolean }> }>
  >(`${API_BASE}/participants/lookup`, { ids: userIds }, options);
  return unwrap(body).items || [];
}

export async function downloadParticipantAvatarBlob(
  userId: string,
  options?: { signal?: AbortSignal },
): Promise<Blob> {
  const response = await fetch(participantAvatarUrl(userId), {
    method: "GET",
    headers: clientHeaders(),
    signal: options?.signal,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Erro HTTP ${response.status}`);
  }
  return response.blob();
}
