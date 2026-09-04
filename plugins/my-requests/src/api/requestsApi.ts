import { httpGet, httpPatch, httpPost, getAccessToken, DELPI_CALLER_APP } from "./httpClient";
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

export type RequestListQuery = {
  signal?: AbortSignal;
  page?: number;
  pageSize?: number;
  typeCode?: string;
  status?: string;
  branch?: string;
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
      "X-Delpi-Caller-App": DELPI_CALLER_APP,
      "Idempotency-Key": input.idempotencyKey,
      ...(getAccessToken() ? { Authorization: `Bearer ${getAccessToken()}` } : {}),
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
  input: { version?: number; returnReason?: string; cancelJustification?: string; idempotencyKey: string },
) {
  const response = await fetch(
    `${API_BASE}/requests/${encodeURIComponent(requestId)}/transitions/${encodeURIComponent(action)}`,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-Delpi-Caller-App": DELPI_CALLER_APP,
        "Idempotency-Key": input.idempotencyKey,
        ...(getAccessToken() ? { Authorization: `Bearer ${getAccessToken()}` } : {}),
      },
      body: JSON.stringify({
        version: input.version,
        return_reason: input.returnReason,
        cancel_justification: input.cancelJustification,
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
  version?: number,
) {
  return unwrap(
    await httpPatch<Envelope<RequestDetail>>(`${API_BASE}/requests/${encodeURIComponent(requestId)}`, {
      payload,
      version,
    }),
  );
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
        "X-Delpi-Caller-App": DELPI_CALLER_APP,
        ...(idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {}),
        ...(getAccessToken() ? { Authorization: `Bearer ${getAccessToken()}` } : {}),
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

export async function listArtifacts(requestId: string, options?: { signal?: AbortSignal }) {
  const body = await httpGet<Envelope<{ items: RequestArtifact[]; total?: number } | RequestArtifact[]>>(
    `${API_BASE}/requests/${encodeURIComponent(requestId)}/artifacts`,
    options,
  );
  const data = unwrap(body);
  return Array.isArray(data) ? data : data.items || [];
}

export function attachmentDownloadUrl(attachmentId: string) {
  return `${API_BASE}/attachments/${encodeURIComponent(attachmentId)}/download`;
}

export function artifactDownloadUrl(artifactId: string) {
  return `${API_BASE}/artifacts/${encodeURIComponent(artifactId)}/download`;
}
