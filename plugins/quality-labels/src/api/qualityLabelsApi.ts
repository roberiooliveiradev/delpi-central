import {
  httpDelete,
  httpGet,
  httpGetBlob,
  httpPatch,
  httpPost,
  httpPostForm,
  httpPut,
} from "./httpClient";
import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import type {
  AuditEventsPage,
  Certificate,
  CertificateSavePayload,
  CreateLabelPayload,
  Inspector,
  LabelsPage,
  OpLookup,
  OpSuggestion,
  QualityLabel,
} from "../types/qualityLabels";

export const QUALITY_LABELS_API_BASE = "/apps/api-delpi/quality/labels";

export async function searchOps(
  term: string,
  branches?: string[],
  signal?: AbortSignal,
): Promise<OpSuggestion[]> {
  const query = new URLSearchParams();
  query.set("q", term);
  if (branches && branches.length > 0) query.set("branches", branches.join(","));
  const response = await httpGet<ApiSuccessResponse<{ items: OpSuggestion[] }>>(
    `${QUALITY_LABELS_API_BASE}/search-ops?${query.toString()}`,
    { signal },
  );
  const data = unwrapApiDelpiEnvelope(response, "Erro ao buscar as OPs.");
  return data.items ?? [];
}

export async function lookupOp(
  productionOrder: string,
  branch?: string,
  signal?: AbortSignal,
): Promise<OpLookup> {
  const query = branch ? `?branch=${encodeURIComponent(branch)}` : "";
  const response = await httpGet<ApiSuccessResponse<OpLookup>>(
    `${QUALITY_LABELS_API_BASE}/lookup-op/${encodeURIComponent(productionOrder)}${query}`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao consultar a OP.");
}

export async function createLabel(
  payload: CreateLabelPayload,
  signal?: AbortSignal,
): Promise<QualityLabel> {
  const response = await httpPost<ApiSuccessResponse<QualityLabel>>(
    QUALITY_LABELS_API_BASE,
    payload,
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao registrar a etiqueta.");
}

export async function listLabels(
  params: { search?: string; branches?: string[]; limit?: number; offset?: number } = {},
  signal?: AbortSignal,
): Promise<LabelsPage> {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (params.branches && params.branches.length > 0)
    query.set("branches", params.branches.join(","));
  if (params.limit != null) query.set("limit", String(params.limit));
  if (params.offset != null) query.set("offset", String(params.offset));
  const qs = query.toString();
  const response = await httpGet<ApiSuccessResponse<LabelsPage>>(
    `${QUALITY_LABELS_API_BASE}${qs ? `?${qs}` : ""}`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao listar as etiquetas.");
}

export async function getLabel(
  labelId: string,
  signal?: AbortSignal,
): Promise<QualityLabel> {
  const response = await httpGet<ApiSuccessResponse<QualityLabel>>(
    `${QUALITY_LABELS_API_BASE}/${labelId}`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao carregar o detalhe da etiqueta.");
}

export async function setLabelActive(
  labelId: string,
  isActive: boolean,
  signal?: AbortSignal,
): Promise<QualityLabel> {
  const response = await httpPatch<ApiSuccessResponse<QualityLabel>>(
    `${QUALITY_LABELS_API_BASE}/${labelId}/active`,
    { isActive },
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao atualizar a etiqueta.");
}

export async function deleteLabel(labelId: string, signal?: AbortSignal): Promise<void> {
  const response = await httpDelete<ApiSuccessResponse<{ id: string; deleted: boolean }>>(
    `${QUALITY_LABELS_API_BASE}/${labelId}`,
    { signal },
  );
  unwrapApiDelpiEnvelope(response, "Erro ao excluir a etiqueta.");
}

export async function listAuditEvents(
  params: {
    search?: string;
    eventTypes?: string[];
    limit?: number;
    offset?: number;
  } = {},
  signal?: AbortSignal,
): Promise<AuditEventsPage> {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (params.eventTypes && params.eventTypes.length > 0)
    query.set("eventTypes", params.eventTypes.join(","));
  if (params.limit != null) query.set("limit", String(params.limit));
  if (params.offset != null) query.set("offset", String(params.offset));
  const qs = query.toString();
  const response = await httpGet<ApiSuccessResponse<AuditEventsPage>>(
    `${QUALITY_LABELS_API_BASE}/audit-events${qs ? `?${qs}` : ""}`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao carregar a auditoria.");
}

export function labelQrUrl(labelId: string): string {
  return `${QUALITY_LABELS_API_BASE}/${labelId}/qr`;
}

export async function fetchLabelQrBlob(labelId: string, signal?: AbortSignal): Promise<Blob> {
  return httpGetBlob(labelQrUrl(labelId), { signal });
}

// ------------------------------------------------------------ Certificado

export async function getCertificate(
  labelId: string,
  signal?: AbortSignal,
): Promise<Certificate> {
  const response = await httpGet<ApiSuccessResponse<Certificate>>(
    `${QUALITY_LABELS_API_BASE}/${labelId}/certificate`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao carregar o certificado.");
}

export async function saveCertificate(
  labelId: string,
  payload: CertificateSavePayload,
  signal?: AbortSignal,
): Promise<Certificate> {
  const response = await httpPut<ApiSuccessResponse<Certificate>>(
    `${QUALITY_LABELS_API_BASE}/${labelId}/certificate`,
    payload,
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao salvar o certificado.");
}

export function certificatePdfUrl(labelId: string): string {
  return `${QUALITY_LABELS_API_BASE}/${labelId}/certificate/pdf`;
}

export async function fetchCertificatePdfBlob(
  labelId: string,
  signal?: AbortSignal,
): Promise<Blob> {
  return httpGetBlob(certificatePdfUrl(labelId), { signal });
}

// -------------------------------------------------------------- Inspetor

export async function getMyInspector(signal?: AbortSignal): Promise<Inspector> {
  const response = await httpGet<ApiSuccessResponse<Inspector>>(
    `${QUALITY_LABELS_API_BASE}/inspectors/me`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao carregar o inspetor.");
}

export async function saveMyInspector(
  payload: { displayName: string; roleTitle?: string | null },
  signal?: AbortSignal,
): Promise<Inspector> {
  const response = await httpPut<ApiSuccessResponse<Inspector>>(
    `${QUALITY_LABELS_API_BASE}/inspectors/me`,
    payload,
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao salvar o inspetor.");
}

export async function uploadMySignature(
  blob: Blob,
  signal?: AbortSignal,
): Promise<Inspector> {
  const formData = new FormData();
  formData.append("signature", blob, "signature.png");
  const response = await httpPostForm<ApiSuccessResponse<Inspector>>(
    `${QUALITY_LABELS_API_BASE}/inspectors/me/signature`,
    formData,
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao registrar a assinatura.");
}

export function inspectorSignatureUrl(): string {
  return `${QUALITY_LABELS_API_BASE}/inspectors/me/signature`;
}

export async function fetchMySignatureBlob(signal?: AbortSignal): Promise<Blob> {
  return httpGetBlob(inspectorSignatureUrl(), { signal });
}
