/**
 * BPMN Modeler API client — convenção `data/api/<context>Api.ts`:
 * fetch + `BPMN_MODELER_API_BASE` + buildAuthHeaders.
 * Toda escrita carrega If-Match (`v{expected_version}`); nunca auto-retry.
 */

export const BPMN_MODELER_API_BASE = "/apps/bpmn-modeler-api";

type GetToken = (() => string | undefined) | undefined;

export type ApiIssue = {
  rule_id: string;
  rule_source: string;
  stage: string;
  severity: "ERROR" | "WARNING" | "INFO";
  message: string;
  element_id: string | null;
  path: string | null;
};

export type ValidationReport = {
  evaluated_stages: string[];
  not_evaluated_stages: string[];
  issues: ApiIssue[];
};

export type ModelSummary = {
  id: string;
  display_name: string;
  version: number;
  created_at: string;
  created_by: string;
  updated_at: string;
  updated_by: string;
  archived_at: string | null;
  /** Revisão mais recente (null = nenhuma revisão criada). */
  latest_revision_number?: number | null;
};

export type ModelListPage = {
  items: ModelSummary[];
  page: number;
  page_size: number;
  has_more: boolean;
};

export type RevisionSummary = {
  revision_number: number;
  artifact_sha256: string;
  origin: "explicit" | "restore";
  source_revision_number?: number | null;
  created_at: string;
  /** Subject técnico (uuid) — nunca exibido como informação primária. */
  created_by: string;
  /** Display name do autor, denormalizado na criação da revisão. */
  created_by_name?: string | null;
  name?: string | null;
  description?: string | null;
};

export type RevisionListPage = {
  items: RevisionSummary[];
  page: number;
  page_size: number;
  has_more: boolean;
};

export type WriteOutcome = {
  model_id: string;
  version: number;
  changed: boolean;
  artifact_sha256: string;
};

export type InspectResult = {
  recognition_state: string;
  eligible_to_import: boolean;
  validation_report: ValidationReport;
};

export type ApiErrorBody = {
  success: false;
  error: {
    code: string;
    message: string;
    recoverable?: boolean;
    details?: Record<string, unknown>;
  };
  meta: { request_id: string };
};

export class BpmnModelerApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId: string;
  readonly details: Record<string, unknown>;

  constructor(status: number, body: ApiErrorBody | null, fallback: string) {
    super(body?.error?.message ?? fallback);
    this.status = status;
    this.code = body?.error?.code ?? "INFRASTRUCTURE_FAILURE";
    this.requestId = body?.meta?.request_id ?? "";
    this.details = body?.error?.details ?? {};
  }
}

async function parseError(response: Response): Promise<never> {
  let body: ApiErrorBody | null = null;
  try {
    body = (await response.json()) as ApiErrorBody;
  } catch {
    body = null;
  }
  throw new BpmnModelerApiError(response.status, body, `HTTP ${response.status}`);
}

function buildAuthHeaders(getAccessToken?: GetToken): HeadersInit {
  const token = getAccessToken?.();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export function etagFor(version: number): string {
  return `"v${version}"`;
}

async function jsonOrThrow<T>(response: Response): Promise<T> {
  if (!response.ok) return parseError(response);
  const body = (await response.json()) as { success: boolean; data: T };
  return body.data;
}

// ---- Queries ----

export type ListModelsParams = {
  query?: string;
  archived?: "active" | "archived" | "all";
  sort?: "updated_at" | "created_at" | "display_name";
  direction?: "asc" | "desc";
  page?: number;
  page_size?: number;
  getAccessToken?: GetToken;
  signal?: AbortSignal;
};

export async function listModels(
  params: ListModelsParams,
): Promise<ModelListPage> {
  const qs = new URLSearchParams();
  if (params.query) qs.set("query", params.query);
  if (params.archived) qs.set("archived", params.archived);
  if (params.sort) qs.set("sort", params.sort);
  if (params.direction) qs.set("direction", params.direction);
  qs.set("page", String(params.page ?? 1));
  qs.set("page_size", String(params.page_size ?? 25));
  const response = await fetch(`${BPMN_MODELER_API_BASE}/models?${qs}`, {
    headers: buildAuthHeaders(params.getAccessToken),
    signal: params.signal,
  });
  return jsonOrThrow<ModelListPage>(response);
}

export async function getModel(
  modelId: string,
  opts: { getAccessToken?: GetToken; signal?: AbortSignal } = {},
): Promise<{ model: ModelSummary; version: number }> {
  const response = await fetch(`${BPMN_MODELER_API_BASE}/models/${modelId}`, {
    headers: buildAuthHeaders(opts.getAccessToken),
    signal: opts.signal,
  });
  if (!response.ok) return parseError(response);
  const body = (await response.json()) as { data: ModelSummary };
  const etag = response.headers.get("etag") ?? "";
  const version = Number(etag.replace(/\D/g, "")) || body.data.version;
  return { model: body.data, version };
}

export async function getWorkingCopy(
  modelId: string,
  opts: { getAccessToken?: GetToken; signal?: AbortSignal } = {},
): Promise<{ xml: string; version: number }> {
  const response = await fetch(
    `${BPMN_MODELER_API_BASE}/models/${modelId}/working-copy`,
    { headers: buildAuthHeaders(opts.getAccessToken), signal: opts.signal },
  );
  if (!response.ok) return parseError(response);
  const xml = await response.text();
  const etag = response.headers.get("etag") ?? "";
  return { xml, version: Number(etag.replace(/\D/g, "")) || 1 };
}

export async function listRevisions(
  modelId: string,
  opts: {
    page?: number;
    page_size?: number;
    getAccessToken?: GetToken;
    signal?: AbortSignal;
  } = {},
): Promise<RevisionListPage> {
  const qs = new URLSearchParams({
    page: String(opts.page ?? 1),
    page_size: String(opts.page_size ?? 25),
  });
  const response = await fetch(
    `${BPMN_MODELER_API_BASE}/models/${modelId}/revisions?${qs}`,
    { headers: buildAuthHeaders(opts.getAccessToken), signal: opts.signal },
  );
  return jsonOrThrow<RevisionListPage>(response);
}

export async function getRevision(
  modelId: string,
  revisionNumber: number,
  opts: { getAccessToken?: GetToken; signal?: AbortSignal } = {},
): Promise<RevisionSummary> {
  const response = await fetch(
    `${BPMN_MODELER_API_BASE}/models/${modelId}/revisions/${revisionNumber}`,
    { headers: buildAuthHeaders(opts.getAccessToken), signal: opts.signal },
  );
  return jsonOrThrow<RevisionSummary>(response);
}

export async function getRevisionXml(
  modelId: string,
  revisionNumber: number,
  opts: { getAccessToken?: GetToken; signal?: AbortSignal } = {},
): Promise<string> {
  const response = await fetch(
    `${BPMN_MODELER_API_BASE}/models/${modelId}/revisions/${revisionNumber}/export`,
    { headers: buildAuthHeaders(opts.getAccessToken), signal: opts.signal },
  );
  if (!response.ok) return parseError(response);
  return response.text();
}

// ---- Mutations (never auto-retried) ----

export async function createModel(
  displayName: string,
  opts: { getAccessToken?: GetToken } = {},
): Promise<WriteOutcome> {
  const response = await fetch(`${BPMN_MODELER_API_BASE}/models`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...buildAuthHeaders(opts.getAccessToken),
    },
    body: JSON.stringify({ display_name: displayName }),
  });
  return jsonOrThrow<WriteOutcome>(response);
}

export async function renameModel(
  modelId: string,
  displayName: string,
  expectedVersion: number,
  opts: { getAccessToken?: GetToken } = {},
): Promise<WriteOutcome> {
  const response = await fetch(`${BPMN_MODELER_API_BASE}/models/${modelId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "If-Match": etagFor(expectedVersion),
      ...buildAuthHeaders(opts.getAccessToken),
    },
    body: JSON.stringify({ display_name: displayName }),
  });
  return jsonOrThrow<WriteOutcome>(response);
}

export async function duplicateModel(
  modelId: string,
  displayName: string,
  opts: { getAccessToken?: GetToken } = {},
): Promise<WriteOutcome> {
  const response = await fetch(
    `${BPMN_MODELER_API_BASE}/models/${modelId}/duplicate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...buildAuthHeaders(opts.getAccessToken),
      },
      body: JSON.stringify({ display_name: displayName }),
    },
  );
  return jsonOrThrow<WriteOutcome>(response);
}

export async function archiveModel(
  modelId: string,
  expectedVersion: number,
  opts: { getAccessToken?: GetToken } = {},
): Promise<WriteOutcome> {
  const response = await fetch(
    `${BPMN_MODELER_API_BASE}/models/${modelId}/archive`,
    {
      method: "POST",
      headers: {
        "If-Match": etagFor(expectedVersion),
        ...buildAuthHeaders(opts.getAccessToken),
      },
    },
  );
  return jsonOrThrow<WriteOutcome>(response);
}

export async function unarchiveModel(
  modelId: string,
  expectedVersion: number,
  opts: { getAccessToken?: GetToken } = {},
): Promise<WriteOutcome> {
  const response = await fetch(
    `${BPMN_MODELER_API_BASE}/models/${modelId}/unarchive`,
    {
      method: "POST",
      headers: {
        "If-Match": etagFor(expectedVersion),
        ...buildAuthHeaders(opts.getAccessToken),
      },
    },
  );
  return jsonOrThrow<WriteOutcome>(response);
}

export async function saveWorkingCopy(
  modelId: string,
  xml: string,
  expectedVersion: number,
  opts: { getAccessToken?: GetToken } = {},
): Promise<WriteOutcome> {
  const response = await fetch(
    `${BPMN_MODELER_API_BASE}/models/${modelId}/working-copy`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/xml; charset=utf-8",
        "If-Match": etagFor(expectedVersion),
        ...buildAuthHeaders(opts.getAccessToken),
      },
      body: xml,
    },
  );
  return jsonOrThrow<WriteOutcome>(response);
}

export async function validateWorkingCopy(
  modelId: string,
  xml: string,
  opts: { getAccessToken?: GetToken } = {},
): Promise<ValidationReport> {
  const response = await fetch(
    `${BPMN_MODELER_API_BASE}/models/${modelId}/working-copy/validate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/xml; charset=utf-8",
        ...buildAuthHeaders(opts.getAccessToken),
      },
      body: xml,
    },
  );
  return jsonOrThrow<ValidationReport>(response);
}

export async function createRevision(
  modelId: string,
  expectedVersion: number,
  opts: { getAccessToken?: GetToken; name?: string; description?: string } = {},
): Promise<{ revision_number: number; version: number }> {
  const { name, description, ...rest } = opts;
  const response = await fetch(
    `${BPMN_MODELER_API_BASE}/models/${modelId}/revisions`,
    {
      method: "POST",
      headers: {
        "If-Match": etagFor(expectedVersion),
        ...(name != null || description != null
          ? { "Content-Type": "application/json" }
          : {}),
        ...buildAuthHeaders(rest.getAccessToken),
      },
      body:
        name != null || description != null
          ? JSON.stringify({ name: name ?? null, description: description ?? null })
          : undefined,
    },
  );
  return jsonOrThrow<{ revision_number: number; version: number }>(response);
}

export async function restoreRevision(
  modelId: string,
  revisionNumber: number,
  expectedVersion: number,
  opts: { getAccessToken?: GetToken } = {},
): Promise<WriteOutcome> {
  const response = await fetch(
    `${BPMN_MODELER_API_BASE}/models/${modelId}/revisions/${revisionNumber}/restore`,
    {
      method: "POST",
      headers: {
        "If-Match": etagFor(expectedVersion),
        ...buildAuthHeaders(opts.getAccessToken),
      },
    },
  );
  return jsonOrThrow<WriteOutcome>(response);
}

// ---- Import / inspect (multipart) ----

export async function inspectImport(
  file: File,
  opts: { getAccessToken?: GetToken } = {},
): Promise<InspectResult> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${BPMN_MODELER_API_BASE}/imports/inspect`, {
    method: "POST",
    headers: buildAuthHeaders(opts.getAccessToken),
    body: form,
  });
  return jsonOrThrow<InspectResult>(response);
}

export async function importModel(
  file: File,
  displayName: string,
  opts: { getAccessToken?: GetToken } = {},
): Promise<WriteOutcome> {
  const form = new FormData();
  form.append("file", file);
  form.append("display_name", displayName);
  const response = await fetch(`${BPMN_MODELER_API_BASE}/models/import`, {
    method: "POST",
    headers: buildAuthHeaders(opts.getAccessToken),
    body: form,
  });
  return jsonOrThrow<WriteOutcome>(response);
}

export async function exportWorkingCopy(
  modelId: string,
  opts: { getAccessToken?: GetToken } = {},
): Promise<string> {
  const response = await fetch(
    `${BPMN_MODELER_API_BASE}/models/${modelId}/working-copy/export`,
    { headers: buildAuthHeaders(opts.getAccessToken) },
  );
  if (!response.ok) return parseError(response);
  return response.text();
}
