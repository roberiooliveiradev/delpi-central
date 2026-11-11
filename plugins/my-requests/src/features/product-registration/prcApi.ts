/** PRC-REF-023-F03/F04 — client do caso oficial PRC na Engineering API.
 *
 * Minhas Solicitações é a experiência do solicitante sobre o mesmo
 * caso governado pela Engineering API — nenhum chamado paralelo é
 * criado no requests-api. Autorização é sempre backend (object AuthZ);
 * aqui só identidade autenticada + contrato.
 */

import {
  ApiClientError,
  authHeaders,
  getAccessToken,
  httpGet,
  httpPatch,
  httpPost,
} from "../../api/httpClient";
import type { Envelope } from "../../types/requests";
import type {
  PrcIntakeBody,
  PrcReferenceData,
} from "@delpi/plugin-ui/index";

const PRC_BASE = "/apps/engineering-api/v1/product-registration";

function unwrap<T>(body: Envelope<T>): T {
  return body.data;
}

// ---------------------------------------------------------------------
// Tipos de resposta (espelho estrutural do contrato).
// ---------------------------------------------------------------------

export type PrcCatalogItem = { code: string; description: string };

export type PrcEditContextField = {
  value: unknown;
  officialField?: string | null;
};

export type PrcEditContextLink = {
  supplierCode: string;
  store: string;
  supplierName?: string;
  supplierShortName?: string;
  partNumber?: string | null;
  catalogNumber?: string | null;
};

export type PrcEditContext = {
  officialCode: string;
  readAt?: string;
  baselineVersion?: number;
  sourceContractVersion?: string;
  fingerprint?: string;
  fields: Record<string, PrcEditContextField>;
  links: PrcEditContextLink[];
  linksComplete?: boolean;
};

export type PrcIntakeResult = {
  requestId: string;
  caseStatus: string;
  createdAt: string;
  source: string;
  requestType: string;
  caseVersion: number;
};

export type PrcRequestSummary = {
  id: string;
  requestType: string;
  status: string;
  requester: { subject: string; displayName?: string | null };
  source: string;
  createdAt: string;
  assignedTo?: string | null;
  officialCode?: string | null;
  caseVersion: number;
};

export type PrcRequestList = {
  items: PrcRequestSummary[];
  page: number;
  pageSize?: number;
  total?: number;
  statusCounts?: Record<string, number>;
};

export type PrcCorrectionTarget = {
  targetType: string;
  targetPath?: string | null;
  targetKey?: string | null;
  reason: string;
};

export type PrcCorrectionReturn = {
  returnId?: string;
  status?: string;
  reason?: string;
  targets?: PrcCorrectionTarget[];
  createdAt?: string;
  resubmittedAt?: string | null;
};

export type PrcAttachment = {
  attachmentId: string;
  requestId: string;
  originalFileName: string;
  mediaType?: string | null;
  sizeBytes?: number | null;
  sha256?: string;
  state: string;
  uploadedByDisplayName?: string | null;
  createdAt?: string;
};

export type PrcTimelineEvent = {
  eventType: string;
  actorDisplayName?: string | null;
  reason?: string | null;
  createdAt: string;
  meta?: Record<string, unknown> | null;
};

export type PrcRequestDetail = {
  id: string;
  status: string;
  requestType: string;
  source: string;
  officialCode?: string | null;
  caseVersion: number;
  requester: { subject: string; displayName?: string | null };
  createdAt: string;
  technicalDraft?: Record<string, unknown> | null;
  requestedPayload?: Record<string, unknown> | null;
  allowedActions: string[];
  correctionExchange?: {
    canCorrect?: boolean;
    canReturn?: boolean;
    openReturn?: { targets?: PrcCorrectionTarget[]; reason?: string } | null;
    lastResubmitted?: unknown;
    requesterAuthz?: { status: string; code?: string | null; note?: string };
  } | null;
};

// ---------------------------------------------------------------------
// Leituras de formulário.
// ---------------------------------------------------------------------

export function fetchPrcReferenceData(
  signal?: AbortSignal,
): Promise<PrcReferenceData> {
  return httpGet<Envelope<PrcReferenceData>>(
    `${PRC_BASE}/reference-data`,
    { signal },
  ).then(unwrap);
}

export function fetchPrcCatalog(
  catalog: string,
  query = "",
  signal?: AbortSignal,
): Promise<PrcCatalogItem[]> {
  const qs = query ? `?query=${encodeURIComponent(query)}` : "";
  return httpGet<Envelope<{ items: PrcCatalogItem[] }>>(
    `${PRC_BASE}/reference-data/catalogs/${encodeURIComponent(catalog)}${qs}`,
    { signal },
  ).then((body) => unwrap(body).items);
}

export type PrcSupplierHit = {
  supplier_code: string;
  supplier_store: string;
  supplier_name?: string;
  supplier_short_name?: string;
};

export function searchPrcSuppliers(
  query: string,
  signal?: AbortSignal,
): Promise<PrcSupplierHit[]> {
  return httpGet<Envelope<{ items: PrcSupplierHit[] }>>(
    `${PRC_BASE}/reference-data/suppliers/search?query=${encodeURIComponent(query)}`,
    { signal },
  ).then((body) => unwrap(body).items);
}

export function fetchPrcEditContext(
  officialCode: string,
  signal?: AbortSignal,
): Promise<PrcEditContext> {
  return httpGet<Envelope<PrcEditContext>>(
    `${PRC_BASE}/reference-data/products/${encodeURIComponent(officialCode)}/edit-context`,
    { signal },
  ).then(unwrap);
}

// ---------------------------------------------------------------------
// Intake e acompanhamento.
// ---------------------------------------------------------------------

export function prcIntakeSubmit(
  body: PrcIntakeBody,
  idempotencyKey: string,
  signal?: AbortSignal,
): Promise<PrcIntakeResult> {
  return httpPost<Envelope<PrcIntakeResult>>(
    `${PRC_BASE}/intake/requests`,
    body,
    { signal, headers: { "Idempotency-Key": idempotencyKey } },
  ).then(unwrap);
}

export function listMyPrcRequests(
  signal?: AbortSignal,
): Promise<PrcRequestList> {
  return httpGet<Envelope<PrcRequestList>>(
    `${PRC_BASE}/requests?pageSize=50`,
    { signal },
  ).then(unwrap);
}

export function fetchPrcRequest(
  requestId: string,
  signal?: AbortSignal,
): Promise<PrcRequestDetail> {
  return httpGet<Envelope<PrcRequestDetail>>(
    `${PRC_BASE}/requests/${encodeURIComponent(requestId)}`,
    { signal },
  ).then(unwrap);
}

export function fetchPrcTimeline(
  requestId: string,
  signal?: AbortSignal,
): Promise<PrcTimelineEvent[]> {
  return httpGet<Envelope<{ items: PrcTimelineEvent[] }>>(
    `${PRC_BASE}/requests/${encodeURIComponent(requestId)}/timeline`,
    { signal },
  ).then((body) => unwrap(body).items);
}

export function fetchPrcCorrectionReturns(
  requestId: string,
  signal?: AbortSignal,
): Promise<PrcCorrectionReturn[]> {
  return httpGet<Envelope<{ items: PrcCorrectionReturn[] }>>(
    `${PRC_BASE}/requests/${encodeURIComponent(requestId)}/correction-returns`,
    { signal },
  ).then((body) => unwrap(body).items);
}

export function savePrcReturnedFields(
  requestId: string,
  expectedVersion: number,
  changes: Array<{
    path: string;
    proposedValue: unknown;
    reason: string;
    mode: "changed" | "confirmed";
  }>,
  idempotencyKey: string,
  signal?: AbortSignal,
): Promise<PrcRequestDetail> {
  return httpPatch<Envelope<PrcRequestDetail>>(
    `${PRC_BASE}/requests/${encodeURIComponent(requestId)}/returned-fields`,
    { expectedVersion, changes },
    { signal, headers: { "Idempotency-Key": idempotencyKey } },
  ).then(unwrap);
}

export function resubmitPrcCorrection(
  requestId: string,
  expectedVersion: number,
  idempotencyKey: string,
  signal?: AbortSignal,
): Promise<PrcRequestDetail> {
  return httpPost<Envelope<PrcRequestDetail>>(
    `${PRC_BASE}/requests/${encodeURIComponent(requestId)}/actions/resubmit-correction`,
    { expectedVersion },
    { signal, headers: { "Idempotency-Key": idempotencyKey } },
  ).then(unwrap);
}

// ---------------------------------------------------------------------
// Anexos (privados — sempre autenticados).
// ---------------------------------------------------------------------

export function fetchPrcAttachments(
  requestId: string,
  signal?: AbortSignal,
): Promise<{ attachments: PrcAttachment[]; canUpload: boolean }> {
  return httpGet<Envelope<{ attachments: PrcAttachment[]; canUpload: boolean }>>(
    `${PRC_BASE}/requests/${encodeURIComponent(requestId)}/attachments`,
    { signal },
  ).then(unwrap);
}

export async function uploadPrcAttachment(
  requestId: string,
  file: File,
): Promise<PrcAttachment> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(
    `${PRC_BASE}/requests/${encodeURIComponent(requestId)}/attachments`,
    {
      method: "POST",
      headers: authHeaders(),
      body: form,
    },
  );
  if (!response.ok) {
    let message = `Falha no upload (${response.status}).`;
    try {
      const body = await response.json();
      message = body?.detail || body?.error?.message || message;
    } catch {
      /* resposta não-JSON */
    }
    throw new ApiClientError(response.status, message);
  }
  const body = (await response.json()) as Envelope<{
    attachment: PrcAttachment;
  }>;
  return body.data.attachment;
}

export async function downloadPrcAttachment(
  requestId: string,
  attachmentId: string,
): Promise<Blob> {
  const token = getAccessToken();
  const response = await fetch(
    `${PRC_BASE}/requests/${encodeURIComponent(requestId)}/attachments/${encodeURIComponent(attachmentId)}/download`,
    { headers: token ? { Authorization: `Bearer ${token}` } : {} },
  );
  if (!response.ok) {
    throw new ApiClientError(
      response.status,
      `Falha no download (${response.status}).`,
    );
  }
  return response.blob();
}
