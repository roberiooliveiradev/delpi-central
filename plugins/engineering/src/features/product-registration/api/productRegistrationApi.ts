/** Cliente do bounded context Product Registration — somente os
 * contratos PRC da Engineering API. O MFE nunca chama api-delpi/TOTVS
 * direto e nunca decide autorização (backend fail-closed). */

import {
  deleteJson,
  getJson,
  patchJson,
  postJson,
} from "../../../api/httpClient";

const BASE = "/apps/engineering-api/v1/product-registration";

export type Envelope<T> = {
  success: boolean;
  message: string;
  data: T;
};

export type PrcQueueResult = {
  items: PrcRequestSummary[];
  page: number;
  pageSize: number;
  total: number;
  statusCounts?: Record<string, number>;
};

export type PrcRequestSummary = {
  id: string;
  requestType: "create" | "update";
  status: string;
  requester: { subject: string; displayName?: string | null };
  source: string;
  createdAt: string;
  assignedTo?: string | null;
  assignedToDisplayName?: string | null;
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
  assignedToDisplayName?: string | null;
  officialCode?: string | null;
  baseRevision?: number | null;
  requestedChanges: Record<string, unknown>;
  technicalDraft?: Record<string, unknown> | null;
  changedPaths: Array<{ path: string; reason: string }>;
  draftVersion?: number;
  caseVersion: number;
  /** D15 — baseline oficial capturado server-side no intake UPDATE. */
  officialBaseline?: {
    baselineVersion?: number;
    sourceContractVersion?: string;
    officialProductCode?: string;
    officialSource?: string;
    readAt?: string;
    capturedAt?: string;
    capturedBy?: string;
    linksComplete?: boolean;
    fingerprint?: string;
    fields?: Record<string, unknown>;
    links?: Array<{
      supplierCode: string;
      store: string;
      supplierName?: string;
      supplierShortName?: string;
      partNumber?: string;
      catalogNumber?: string;
    }>;
    removeCompletionPolicy?: string;
  } | null;
  removeCompletionPolicy?: string;
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
  actor_display_name?: string | null;
  actor_email?: string | null;
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
): Promise<Envelope<PrcQueueResult>> {
  return getJson(`${BASE}/requests${qs(filters)}`, signal);
}

export type PrcCatalogItem = {
  code: string;
  label: string;
  disabled?: number;
};

export async function fetchPrcCatalog(
  catalog: string,
  query?: string,
  signal?: AbortSignal,
  limit?: number,
): Promise<Envelope<{ items: PrcCatalogItem[]; hasMore: boolean }>> {
  const qs = new URLSearchParams();
  if (query) qs.set("query", query);
  if (limit) qs.set("limit", String(limit));
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return getJson(
    `${BASE}/reference-data/catalogs/${catalog}${suffix}`,
    signal,
  );
}

export type PrcSupplierHit = {
  supplier_code?: string;
  supplier_store?: string;
  supplier_name?: string;
  supplier_short_name?: string;
  [key: string]: unknown;
};

export async function searchPrcSuppliers(
  query: string,
  signal?: AbortSignal,
): Promise<Envelope<{ items: PrcSupplierHit[]; total?: number }>> {
  const qs = new URLSearchParams({ query });
  return getJson(
    `${BASE}/reference-data/suppliers/search?${qs.toString()}`,
    signal,
  );
}

export type PrcEditContextField = {
  value: unknown;
  officialField?: string | null;
};

export type PrcEditContextLink = {
  supplierCode: string;
  store: string;
  supplierName: string;
  supplierShortName?: string;
  partNumber: string;
  catalogNumber: string;
};

export type PrcEditContext = {
  status: string;
  officialCode: string;
  readAt?: string;
  baselineVersion?: number;
  sourceContractVersion?: string;
  fingerprint?: string;
  fields: Record<string, PrcEditContextField>;
  links: PrcEditContextLink[];
  linksComplete?: boolean;
  removeCompletionPolicy?: string;
};

export type PrcSupplierLinkChange = {
  operation: "update" | "add" | "remove";
  key: { supplierCode: string; store: string };
  fields: { partNumber?: string; catalogNumber?: string };
  reason?: string;
  fieldReasons?: { partNumber?: string; catalogNumber?: string };
};

export async function fetchPrcEditContext(
  officialCode: string,
  signal?: AbortSignal,
): Promise<Envelope<PrcEditContext>> {
  return getJson(
    `${BASE}/reference-data/products/${encodeURIComponent(
      officialCode.trim(),
    )}/edit-context`,
    signal,
  );
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
  /** REF-001 — resolvido pela Engineering API; nunca pedido ao usuário. */
  baseRevision?: number | null;
  changes?: Array<{ path: string; proposedValue: unknown; reason: string }> | null;
  /** D12 — operações granulares de vínculo SA5 (update/add). */
  supplierLinkChanges?: PrcSupplierLinkChange[] | null;
  /** D14-FIX — justificativas opcionais do create (≤250): por path
   * preenchido e por vínculo incluído; canal próprio, nunca dentro de
   * requestedData/suppliers[]. */
  reasons?: {
    fields?: Record<string, string>;
    supplierLinks?: Array<{
      key: { supplierCode: string; store: string };
      reason?: string;
      fieldReasons?: { partNumber?: string; catalogNumber?: string };
    }>;
  } | null;
  /** D15 — fingerprint do edit-context para concorrência oficial. */
  baselineFingerprint?: string | null;
  editContextReadAt?: string | null;
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

/* --- D16 attendance flags ------------------------------------------------ */

export type PrcFlagTargetAttribute = "partNumber" | "catalogNumber";

export type PrcAttendanceFlag = {
  id: string;
  requestId: string;
  title: string;
  description: string;
  status: "OPEN" | "RESOLVED";
  subject: "GENERAL" | "FIELD" | "SUPPLIER_LINK";
  targetPath?: string | null;
  targetAttribute?: PrcFlagTargetAttribute | null;
  targetKey?: string | null;
  supplierKey?: { supplierCode: string; store: string } | null;
  version: number;
  createdAt: string;
  createdBy: { subject: string; displayName?: string | null };
  updatedAt: string;
  updatedBy: { subject?: string | null; displayName?: string | null };
  resolvedAt?: string | null;
  resolvedBy?: { subject: string; displayName?: string | null } | null;
  deleted?: boolean;
  legacyGeneral?: boolean;
  productCode?: string | null;
  requestType?: string | null;
  requestStatus?: string | null;
  productDescription?: string | null;
};

export type PrcFlagListResult = {
  items: PrcAttendanceFlag[];
  page: number;
  pageSize: number;
  total: number;
  openCount: number;
  resolvedCount: number;
  hasMore: boolean;
  distinctRequestCount?: number;
  distinctProductCount?: number;
};

export type PrcFlagSummaryResult = {
  groupBy: string;
  items: Array<{
    key: string;
    flagCount: number;
    openCount: number;
    resolvedCount: number;
    requestCount: number;
    lastCreatedAt?: string | null;
  }>;
  page: number;
  pageSize: number;
  total: number;
  openCount: number;
  resolvedCount: number;
  distinctRequestCount: number;
  distinctProductCount: number;
  hasMore: boolean;
};

export type PrcFlagCreateBody = {
  title: string;
  description: string;
  subject?: "FIELD" | "SUPPLIER_LINK";
  targetPath?: string | null;
  targetAttribute?: PrcFlagTargetAttribute | null;
  supplierKey?: { supplierCode: string; store: string } | null;
};

export type PrcFlagUpdateBody = {
  expectedVersion: number;
  title?: string;
  description?: string;
};

export type PrcFlagListParams = {
  status?: "OPEN" | "RESOLVED" | "all";
  subject?: string;
  targetPath?: string;
  targetAttribute?: string;
  supplierCode?: string;
  store?: string;
  page?: number;
  pageSize?: number;
};

export async function fetchPrcFlags(
  requestId: string,
  params?: PrcFlagListParams,
  signal?: AbortSignal,
): Promise<Envelope<PrcFlagListResult>> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set("status", params.status);
  if (params?.subject) qs.set("subject", params.subject);
  if (params?.targetPath) qs.set("targetPath", params.targetPath);
  if (params?.targetAttribute) qs.set("targetAttribute", params.targetAttribute);
  if (params?.supplierCode) qs.set("supplierCode", params.supplierCode);
  if (params?.store) qs.set("store", params.store);
  if (params?.page) qs.set("page", String(params.page));
  if (params?.pageSize) qs.set("pageSize", String(params.pageSize));
  const suffix = qs.toString() ? `?${qs}` : "";
  return getJson(
    `${BASE}/requests/${requestId}/flags${suffix}`,
    signal,
  );
}

export type PrcFlagCrossParams = PrcFlagListParams & {
  productCode?: string;
  requestId?: string;
  requestType?: string;
  requestStatus?: string;
  assignee?: string;
  createdFrom?: string;
  createdTo?: string;
};

export async function fetchPrcFlagsCrossCase(
  params?: PrcFlagCrossParams,
  signal?: AbortSignal,
): Promise<Envelope<PrcFlagListResult>> {
  const qs = new URLSearchParams();
  const entries: Array<[string, string | undefined]> = [
    ["status", params?.status],
    ["subject", params?.subject],
    ["targetPath", params?.targetPath],
    ["targetAttribute", params?.targetAttribute],
    ["productCode", params?.productCode],
    ["requestId", params?.requestId],
    ["requestType", params?.requestType],
    ["requestStatus", params?.requestStatus],
    ["assignee", params?.assignee],
    ["supplierCode", params?.supplierCode],
    ["store", params?.store],
    ["createdFrom", params?.createdFrom],
    ["createdTo", params?.createdTo],
  ];
  for (const [k, v] of entries) {
    if (v) qs.set(k, v);
  }
  if (params?.page) qs.set("page", String(params.page));
  if (params?.pageSize) qs.set("pageSize", String(params.pageSize));
  const suffix = qs.toString() ? `?${qs}` : "";
  return getJson(`${BASE}/flags${suffix}`, signal);
}

export async function fetchPrcFlagsSummary(
  params?: {
    groupBy?: string;
    status?: string;
    subject?: string;
    targetPath?: string;
    targetAttribute?: string;
    productCode?: string;
    requestStatus?: string;
    page?: number;
    pageSize?: number;
  },
  signal?: AbortSignal,
): Promise<Envelope<PrcFlagSummaryResult>> {
  const qs = new URLSearchParams();
  if (params?.groupBy) qs.set("groupBy", params.groupBy);
  if (params?.status) qs.set("status", params.status);
  if (params?.subject) qs.set("subject", params.subject);
  if (params?.targetPath) qs.set("targetPath", params.targetPath);
  if (params?.targetAttribute) qs.set("targetAttribute", params.targetAttribute);
  if (params?.productCode) qs.set("productCode", params.productCode);
  if (params?.requestStatus) qs.set("requestStatus", params.requestStatus);
  if (params?.page) qs.set("page", String(params.page));
  if (params?.pageSize) qs.set("pageSize", String(params.pageSize));
  const suffix = qs.toString() ? `?${qs}` : "";
  return getJson(`${BASE}/flags/summary${suffix}`, signal);
}

export async function createPrcFlag(
  requestId: string,
  body: PrcFlagCreateBody,
  idempotencyKey: string,
): Promise<Envelope<PrcAttendanceFlag>> {
  return postJson(`${BASE}/requests/${requestId}/flags`, body, undefined, {
    headers: { "Idempotency-Key": idempotencyKey },
  });
}

export async function updatePrcFlag(
  requestId: string,
  flagId: string,
  body: PrcFlagUpdateBody,
  idempotencyKey?: string,
): Promise<Envelope<PrcAttendanceFlag>> {
  return patchJson(
    `${BASE}/requests/${requestId}/flags/${flagId}`,
    body,
    undefined,
    idempotencyKey
      ? { headers: { "Idempotency-Key": idempotencyKey } }
      : undefined,
  );
}

export async function resolvePrcFlag(
  requestId: string,
  flagId: string,
  body: { expectedVersion: number; reason?: string },
  idempotencyKey?: string,
): Promise<Envelope<PrcAttendanceFlag>> {
  return postJson(
    `${BASE}/requests/${requestId}/flags/${flagId}/actions/resolve`,
    body,
    undefined,
    idempotencyKey
      ? { headers: { "Idempotency-Key": idempotencyKey } }
      : undefined,
  );
}

export async function reopenPrcFlag(
  requestId: string,
  flagId: string,
  body: { expectedVersion: number; reason?: string },
  idempotencyKey?: string,
): Promise<Envelope<PrcAttendanceFlag>> {
  return postJson(
    `${BASE}/requests/${requestId}/flags/${flagId}/actions/reopen`,
    body,
    undefined,
    idempotencyKey
      ? { headers: { "Idempotency-Key": idempotencyKey } }
      : undefined,
  );
}

export async function deletePrcFlag(
  requestId: string,
  flagId: string,
  expectedVersion: number,
  idempotencyKey?: string,
): Promise<Envelope<{ id: string; requestId: string; deleted: boolean; version: number }>> {
  return deleteJson(
    `${BASE}/requests/${requestId}/flags/${flagId}?expectedVersion=${expectedVersion}`,
    undefined,
    idempotencyKey
      ? { headers: { "Idempotency-Key": idempotencyKey } }
      : undefined,
  );
}
