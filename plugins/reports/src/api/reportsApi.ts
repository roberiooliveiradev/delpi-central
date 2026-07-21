import { httpDelete, httpGet, httpPatch, httpPost, httpPut } from "./httpClient";
import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import type {
  DirectoryUser,
  ReportDefinition,
  ReportDefinitionsList,
  ReportRecipient,
  ReportRun,
  ReportSchedule,
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
