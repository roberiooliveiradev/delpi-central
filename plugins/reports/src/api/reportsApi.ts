import { httpDelete, httpGet, httpPatch, httpPost, httpPut } from "./httpClient";
import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import type {
  DirectoryUser,
  ReportDefinition,
  ReportDefinitionsList,
  ReportProviderInfo,
  ReportRecipient,
  ReportRun,
  ReportSchedule,
  ShortageItemNote,
  ShortageItemNotesList,
  ShortagePreviewItem,
} from "../types/reports";

export const REPORTS_API_BASE = "/apps/api-delpi/reports";

export async function listReportDefinitions(
  signal?: AbortSignal,
): Promise<ReportDefinitionsList> {
  const response = await httpGet<ApiSuccessResponse<ReportDefinitionsList>>(
    `${REPORTS_API_BASE}/definitions`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(
    response,
    "Erro ao carregar definições de relatório.",
  );
}

export async function getReportDefinition(
  definitionId: string,
  signal?: AbortSignal,
): Promise<ReportDefinition> {
  const response = await httpGet<ApiSuccessResponse<ReportDefinition>>(
    `${REPORTS_API_BASE}/definitions/${encodeURIComponent(definitionId)}`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(
    response,
    "Erro ao carregar definição de relatório.",
  );
}

export async function createReportDefinition(body: {
  name: string;
  providerKey: string;
  params: Record<string, unknown>;
  active: boolean;
}): Promise<ReportDefinition> {
  const response = await httpPost<ApiSuccessResponse<ReportDefinition>>(
    `${REPORTS_API_BASE}/definitions`,
    body,
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao criar definição.");
}

export async function updateReportDefinition(
  definitionId: string,
  body: {
    name?: string;
    providerKey?: string;
    params?: Record<string, unknown>;
    active?: boolean;
  },
): Promise<ReportDefinition> {
  const response = await httpPatch<ApiSuccessResponse<ReportDefinition>>(
    `${REPORTS_API_BASE}/definitions/${encodeURIComponent(definitionId)}`,
    body,
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao atualizar definição.");
}

export async function listReportRecipients(
  definitionId: string,
  signal?: AbortSignal,
): Promise<{ items: ReportRecipient[]; total: number }> {
  const response = await httpGet<
    ApiSuccessResponse<{ items: ReportRecipient[]; total: number }>
  >(
    `${REPORTS_API_BASE}/definitions/${encodeURIComponent(definitionId)}/recipients`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao carregar destinatários.");
}

export async function replaceReportRecipients(
  definitionId: string,
  items: Array<{ userId: string; email: string }>,
): Promise<{ items: ReportRecipient[]; total: number }> {
  const response = await httpPut<
    ApiSuccessResponse<{ items: ReportRecipient[]; total: number }>
  >(
    `${REPORTS_API_BASE}/definitions/${encodeURIComponent(definitionId)}/recipients`,
    { items },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao salvar destinatários.");
}

export async function getReportSchedule(
  definitionId: string,
  signal?: AbortSignal,
): Promise<ReportSchedule | null> {
  const response = await httpGet<ApiSuccessResponse<ReportSchedule | null>>(
    `${REPORTS_API_BASE}/definitions/${encodeURIComponent(definitionId)}/schedule`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao carregar agenda.");
}

export async function upsertReportSchedule(
  definitionId: string,
  body: {
    scheduleKind: string;
    hour: number;
    minute: number;
    weekday?: number | null;
    dayOfMonth?: number | null;
    enabled: boolean;
  },
): Promise<ReportSchedule> {
  const response = await httpPut<ApiSuccessResponse<ReportSchedule>>(
    `${REPORTS_API_BASE}/definitions/${encodeURIComponent(definitionId)}/schedule`,
    body,
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao salvar agenda.");
}

export async function deleteReportSchedule(definitionId: string): Promise<void> {
  await httpDelete(
    `${REPORTS_API_BASE}/definitions/${encodeURIComponent(definitionId)}/schedule`,
  );
}

export async function runReportDefinition(
  definitionId: string,
): Promise<ReportRun> {
  const response = await httpPost<ApiSuccessResponse<ReportRun>>(
    `${REPORTS_API_BASE}/definitions/${encodeURIComponent(definitionId)}/run`,
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao executar relatório.");
}

export async function listReportRuns(
  definitionId?: string,
  signal?: AbortSignal,
): Promise<{ items: ReportRun[]; total: number }> {
  const qs = definitionId
    ? `?definitionId=${encodeURIComponent(definitionId)}`
    : "";
  const response = await httpGet<
    ApiSuccessResponse<{ items: ReportRun[]; total: number }>
  >(`${REPORTS_API_BASE}/runs${qs}`, { signal });
  return unwrapApiDelpiEnvelope(response, "Erro ao carregar execuções.");
}

export async function listShortageItemNotes(
  definitionId: string,
  signal?: AbortSignal,
): Promise<ShortageItemNotesList> {
  const response = await httpGet<ApiSuccessResponse<ShortageItemNotesList>>(
    `${REPORTS_API_BASE}/definitions/${encodeURIComponent(definitionId)}/item-notes`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(
    response,
    "Erro ao carregar acompanhamentos.",
  );
}

export async function upsertShortageItemNote(
  definitionId: string,
  productCode: string,
  body: {
    noteText: string;
    authorDisplayName?: string;
    expectedReceiptDate?: string | null;
  },
): Promise<ShortageItemNote> {
  const response = await httpPut<ApiSuccessResponse<ShortageItemNote>>(
    `${REPORTS_API_BASE}/definitions/${encodeURIComponent(definitionId)}/item-notes/${encodeURIComponent(productCode)}`,
    {
      noteText: body.noteText,
      authorDisplayName: body.authorDisplayName,
      expectedReceiptDate: body.expectedReceiptDate || null,
    },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao gravar acompanhamento.");
}

export async function deleteShortageItemNote(
  definitionId: string,
  productCode: string,
): Promise<void> {
  await httpDelete(
    `${REPORTS_API_BASE}/definitions/${encodeURIComponent(definitionId)}/item-notes/${encodeURIComponent(productCode)}`,
  );
}

export async function listReportProviders(
  signal?: AbortSignal,
): Promise<{ items: ReportProviderInfo[]; total: number }> {
  const response = await httpGet<
    ApiSuccessResponse<{ items: ReportProviderInfo[]; total: number }>
  >(`${REPORTS_API_BASE}/providers`, { signal });
  return unwrapApiDelpiEnvelope(response, "Erro ao listar providers.");
}

export async function previewShortage30d(
  params: {
    branch: string;
    horizonDays?: number;
    definitionId?: string;
  },
  signal?: AbortSignal,
): Promise<{
  items: ShortagePreviewItem[];
  total: number;
  title?: string;
}> {
  const qs = new URLSearchParams({
    branch: params.branch,
    horizonDays: String(params.horizonDays ?? 30),
  });
  if (params.definitionId) {
    qs.set("definitionId", params.definitionId);
  }
  const response = await httpGet<
    ApiSuccessResponse<{
      items: ShortagePreviewItem[];
      total: number;
      title?: string;
    }>
  >(
    `${REPORTS_API_BASE}/providers/safety_stock_shortage_30d/preview?${qs.toString()}`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao gerar preview.");
}

export async function searchDirectoryUsers(
  query: string,
  limit = 10,
  signal?: AbortSignal,
): Promise<DirectoryUser[]> {
  const qs = new URLSearchParams({
    q: query,
    limit: String(limit),
    include_self: "true",
    // SMTP real para envio de e-mail (Core mascara por padrão — LGPD).
    reveal_email: "true",
  });
  const payload = await httpGet<{ items?: DirectoryUser[] }>(
    `/core-api/me/directory/users?${qs.toString()}`,
    { signal },
  );
  return payload.items ?? [];
}
