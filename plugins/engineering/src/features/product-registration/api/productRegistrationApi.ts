/** Cliente do bounded context Product Registration — somente os
 * contratos PRC da Engineering API. O MFE nunca chama api-delpi/TOTVS
 * direto e nunca decide autorização (backend fail-closed). */

import { getJson, patchJson, postJson } from "../../../api/httpClient";

const BASE = "/apps/engineering-api/v1/product-registration";

export type Envelope<T> = {
  success: boolean;
  message: string;
  data: T;
};

export type PrcRequestSummary = {
  id: string;
  requestType: "create" | "update";
  status: string;
  requester: { subject: string; displayName?: string | null };
  source: string;
  createdAt: string;
  assignedTo?: string | null;
  officialCode?: string | null;
  caseVersion: number;
};

export type PrcRequestDetail = {
  id: string;
  requestType: "create" | "update";
  productType: string;
  status: string;
  source: string;
  externalRequestId?: string | null;
  requester: { subject: string; displayName?: string | null };
  assignedTo?: string | null;
  officialCode?: string | null;
  baseRevision?: number | null;
  requestedChanges: Record<string, unknown>;
  technicalDraft?: Record<string, unknown> | null;
  changedPaths: Array<{ path: string; reason: string }>;
  draftVersion?: number;
  caseVersion: number;
  allowedActions: string[];
  verificationSummary?: {
    result: string;
    checkedAt: string;
    officialSource: string;
  } | null;
  createdAt: string;
  updatedAt: string;
  completedRecordId?: string | null;
};

export type PrcTimelineEvent = {
  id: string;
  sequence_number: number;
  event_type: string;
  actor_subject: string;
  occurred_at: string;
  reason?: string | null;
  metadata: Record<string, unknown>;
  previous_status?: string | null;
  next_status?: string | null;
};

/** Resultado por campo devolvido pelo backend em `field_results` —
 * o MFE nunca calcula match próprio. */
export type PrcFieldResult = {
  result?: string;
  officialField?: string | null;
  expected?: unknown;
  observed?: unknown;
  reason?: string;
  fields?: string[];
  detail?: Array<{ key: string; result: string; fields?: string[] }>;
};

export type PrcVerification = {
  id: string;
  request_id?: string;
  official_product_code: string;
  requested_by_subject?: string;
  checked_at: string;
  official_source?: string;
  result: string;
  expected_fields?: string[];
  field_results: Record<string, PrcFieldResult>;
  evidence_fingerprint?: string;
  correlation_id?: string;
  error_code?: string | null;
};

export type PrcRecord = {
  id: string;
  official_product_code: string;
  current_revision_number: number;
  last_official_verified_at: string;
  official_source: string;
};

/** Índice de revisões (rota 14) — sem snapshot. */
export type PrcRevisionSummary = {
  revisionNumber: number;
  requestId: string;
  approvedBy: string;
  approvedAt: string;
  changedPaths: string[];
};

/** Snapshot imutável (rota 15) — read-only. */
export type PrcRevisionDetail = {
  id: string;
  record_id: string;
  revision_number: number;
  request_id: string;
  schema_version: number;
  technical_snapshot: Record<string, unknown>;
  changes: Array<{
    path: string;
    before: unknown;
    after: unknown;
    reason: string;
  }>;
  official_evidence_id?: string;
  approved_by_subject: string;
  approved_at: string;
  created_at?: string;
};

export type PrcFieldSpec = {
  path: string;
  kind: string;
  requiredCreateIntake: boolean;
  verifiable: boolean;
  officialField?: string | null;
  enumValues?: string[] | null;
  maxLength: number;
  note?: string | null;
};

export type PrcReferenceData = {
  schemaVersion: number;
  productTypes: string[];
  requestTypes: string[];
  statuses: string[];
  sources: string[];
  fields: PrcFieldSpec[];
  editableDraftPaths: string[];
  supplierKeys: { required: string[]; optional: string[] };
};

function qs(params: Record<string, unknown>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}

export async function fetchPrcQueue(
  filters: Record<string, unknown>,
  signal?: AbortSignal,
): Promise<Envelope<{ items: PrcRequestSummary[]; page: number; pageSize: number; total: number }>> {
  return getJson(`${BASE}/requests${qs(filters)}`, signal);
}

export async function fetchPrcRequest(
  requestId: string,
  signal?: AbortSignal,
): Promise<Envelope<PrcRequestDetail>> {
  return getJson(`${BASE}/requests/${requestId}`, signal);
}

export async function fetchPrcTimeline(
  requestId: string,
  signal?: AbortSignal,
): Promise<Envelope<{ items: PrcTimelineEvent[]; total: number }>> {
  return getJson(`${BASE}/requests/${requestId}/timeline?pageSize=100`, signal);
}

export async function fetchPrcVerifications(
  requestId: string,
  signal?: AbortSignal,
): Promise<Envelope<{ items: PrcVerification[]; total: number }>> {
  return getJson(`${BASE}/requests/${requestId}/verifications`, signal);
}

export async function fetchPrcRecord(
  recordId: string,
  signal?: AbortSignal,
): Promise<Envelope<PrcRecord>> {
  return getJson(`${BASE}/technical-records/${recordId}`, signal);
}

export async function fetchPrcRevisions(
  recordId: string,
  signal?: AbortSignal,
): Promise<Envelope<{ items: PrcRevisionSummary[]; total: number }>> {
  return getJson(`${BASE}/technical-records/${recordId}/revisions`, signal);
}

export async function fetchPrcRevision(
  recordId: string,
  revisionNumber: number,
  signal?: AbortSignal,
): Promise<Envelope<PrcRevisionDetail>> {
  return getJson(
    `${BASE}/technical-records/${recordId}/revisions/${revisionNumber}`,
    signal,
  );
}

export async function fetchPrcReferenceData(
  signal?: AbortSignal,
): Promise<Envelope<PrcReferenceData>> {
  return getJson(`${BASE}/reference-data`, signal);
}

/** Intake 01 — POST create/update. `Idempotency-Key` é contrato
 * obrigatório para retry seguro (replay retorna o mesmo caso). */
export type PrcIntakeBody = {
  source: string;
  externalRequestId?: string | null;
  externalItemId?: string | null;
  requestType: "create" | "update";
  productType: string;
  schemaVersion: number;
  requestedData?: Record<string, unknown> | null;
  officialProductCode?: string | null;
  baseRevision?: number | null;
  changes?: Array<{ path: string; proposedValue: unknown; reason: string }> | null;
};

export type PrcIntakeResult = {
  requestId: string;
  caseStatus: string;
  createdAt: string;
  source: string;
  requestType: string;
  caseVersion: number;
};

export async function prcIntakeSubmit(
  body: PrcIntakeBody,
  idempotencyKey: string,
): Promise<Envelope<PrcIntakeResult>> {
  return postJson(`${BASE}/intake/requests`, body, undefined, {
    headers: { "Idempotency-Key": idempotencyKey },
  });
}

export async function prcAction(
  requestId: string,
  actionPath: string,
  body: Record<string, unknown>,
  idempotencyKey?: string,
): Promise<Envelope<PrcRequestDetail>> {
  return postJson(
    `${BASE}/requests/${requestId}/actions/${actionPath}`,
    body,
    undefined,
    idempotencyKey
      ? { headers: { "Idempotency-Key": idempotencyKey } }
      : undefined,
  );
}

export async function prcUpdateDraft(
  requestId: string,
  body: { expectedVersion: number; changes: Array<{ path: string; proposedValue: unknown; reason: string }> },
  idempotencyKey?: string,
): Promise<Envelope<PrcRequestDetail>> {
  return patchJson(
    `${BASE}/requests/${requestId}/draft`,
    body,
    undefined,
    idempotencyKey
      ? { headers: { "Idempotency-Key": idempotencyKey } }
      : undefined,
  );
}
