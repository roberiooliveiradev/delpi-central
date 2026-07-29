import {
  authBearerHeader,
  httpDelete,
  httpGet,
  httpPatch,
  httpPost,
  httpPostForm,
  httpPut,
  unwrapApiDelpiEnvelope,
  type ApiEnvelope,
} from "./httpClient";
import type {
  KaizenAuditEntry,
  KaizenEvidence,
  KaizenEvidenceStage,
  KaizenEvidenceType,
  KaizenHistoryEvent,
  KaizenListResponse,
  KaizenRecord,
  KaizenRevision,
  KaizenSavingsTimeline,
  KaizenSummary,
} from "../types/kaizen";

const API_BASE = "/apps/api-delpi/quality/kaizens/records";

type ListParams = {
  branch?: string;
  status?: string;
  savings_type?: string;
  title?: string;
  page?: number;
  page_size?: number;
};

function buildQuery(params: ListParams): string {
  const search = new URLSearchParams();
  if (params.branch) search.set("branch", params.branch);
  if (params.status) search.set("status", params.status);
  if (params.savings_type) search.set("savings_type", params.savings_type);
  if (params.title) search.set("title", params.title);
  if (params.page) search.set("page", String(params.page));
  if (params.page_size) search.set("page_size", String(params.page_size));
  const query = search.toString();
  return query ? `?${query}` : "";
}

export async function fetchKaizenRecords(params: ListParams = {}): Promise<KaizenListResponse> {
  const envelope = await httpGet<ApiEnvelope<KaizenListResponse>>(
    `${API_BASE}${buildQuery(params)}`,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao listar kaizens.");
}

export type SummaryParams = {
  branch?: string;
  dateStart?: string;
  dateEnd?: string;
};

/** Indicadores agregados do painel, calculados no backend (Postgres). */
export async function fetchKaizenSummary(params: SummaryParams = {}): Promise<KaizenSummary> {
  const search = new URLSearchParams();
  if (params.branch) search.set("branch", params.branch);
  if (params.dateStart) search.set("start_date", params.dateStart);
  if (params.dateEnd) search.set("end_date", params.dateEnd);
  const query = search.toString();
  const envelope = await httpGet<ApiEnvelope<KaizenSummary>>(
    `${API_BASE}/summary${query ? `?${query}` : ""}`,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao carregar indicadores de kaizen.");
}

export async function fetchKaizenRecord(id: string): Promise<KaizenRecord> {
  const envelope = await httpGet<ApiEnvelope<KaizenRecord>>(`${API_BASE}/${id}`);
  return unwrapApiDelpiEnvelope(envelope, "Erro ao buscar kaizen.");
}

export async function createKaizenRecord(payload: Record<string, unknown>): Promise<KaizenRecord> {
  const envelope = await httpPost<ApiEnvelope<KaizenRecord>>(API_BASE, payload);
  return unwrapApiDelpiEnvelope(envelope, "Erro ao cadastrar kaizen.");
}

export async function updateKaizenRecord(
  id: string,
  payload: Record<string, unknown>,
): Promise<KaizenRecord> {
  const envelope = await httpPut<ApiEnvelope<KaizenRecord>>(`${API_BASE}/${id}`, payload);
  return unwrapApiDelpiEnvelope(envelope, "Erro ao atualizar kaizen.");
}

export async function deleteKaizenRecord(id: string): Promise<void> {
  const envelope = await httpDelete<ApiEnvelope<{ id: string; deleted: boolean }>>(
    `${API_BASE}/${id}`,
  );
  unwrapApiDelpiEnvelope(envelope, "Erro ao excluir kaizen.");
}

// ---------------------------------------------------------------- exportar / importar JSON

export type KaizenExportFile = {
  version: number;
  generated_at?: string;
  source?: string;
  count: number;
  items: Array<Record<string, unknown>>;
};

export type ImportKaizensResult = {
  created: number;
  skipped: number;
  errors: number;
  items: Array<Record<string, unknown>>;
};

export async function exportKaizenRecords(): Promise<KaizenExportFile> {
  const envelope = await httpGet<ApiEnvelope<KaizenExportFile>>(`${API_BASE}/export`);
  return unwrapApiDelpiEnvelope(envelope, "Erro ao exportar kaizens.");
}

export async function importKaizenRecords(
  items: Array<Record<string, unknown>>,
  options: { dryRun?: boolean; skipExisting?: boolean } = {},
): Promise<ImportKaizensResult> {
  const envelope = await httpPost<ApiEnvelope<ImportKaizensResult>>(`${API_BASE}/import`, {
    items,
    dry_run: options.dryRun ?? false,
    skip_existing: options.skipExisting ?? true,
  });
  return unwrapApiDelpiEnvelope(envelope, "Erro ao importar kaizens.");
}

// ---------------------------------------------------------------- revisões

export async function fetchKaizenRevisions(id: string): Promise<KaizenRevision[]> {
  const envelope = await httpGet<ApiEnvelope<{ items: KaizenRevision[] }>>(
    `${API_BASE}/${id}/revisions`,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao listar revisões.").items;
}

// ---------------------------------------------------------------- versões (ciclo de vida)

export async function createKaizenVersion(
  id: string,
  payload: Record<string, unknown>,
): Promise<KaizenRevision> {
  const envelope = await httpPost<ApiEnvelope<KaizenRevision>>(
    `${API_BASE}/${id}/versions`,
    payload,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao criar versão do kaizen.");
}

export async function updateKaizenVersion(
  id: string,
  revisionNumber: number,
  payload: Record<string, unknown>,
): Promise<KaizenRevision> {
  const envelope = await httpPut<ApiEnvelope<KaizenRevision>>(
    `${API_BASE}/${id}/versions/${revisionNumber}`,
    payload,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao atualizar versão do kaizen.");
}

export async function implementKaizenVersion(
  id: string,
  revisionNumber: number,
  payload: { effective_from?: string } = {},
): Promise<KaizenRecord> {
  const envelope = await httpPost<ApiEnvelope<KaizenRecord>>(
    `${API_BASE}/${id}/versions/${revisionNumber}/implement`,
    payload,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao implantar versão do kaizen.");
}

export async function deleteKaizenVersion(id: string, revisionNumber: number): Promise<void> {
  const envelope = await httpDelete<ApiEnvelope<{ deleted: boolean }>>(
    `${API_BASE}/${id}/versions/${revisionNumber}`,
  );
  unwrapApiDelpiEnvelope(envelope, "Erro ao excluir versão do kaizen.");
}

// ---------------------------------------------------------------- registro de alterações

export async function fetchKaizenHistory(id: string): Promise<KaizenHistoryEvent[]> {
  const envelope = await httpGet<ApiEnvelope<{ items: KaizenHistoryEvent[] }>>(
    `${API_BASE}/${id}/history`,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao listar histórico.").items;
}

export async function fetchKaizenAuditLog(id: string): Promise<KaizenAuditEntry[]> {
  const envelope = await httpGet<ApiEnvelope<{ items: KaizenAuditEntry[] }>>(
    `${API_BASE}/${id}/audit-log`,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao listar auditoria.").items;
}

export async function fetchKaizenSavingsTimeline(
  id: string,
  params: { dateStart?: string; dateEnd?: string } = {},
): Promise<KaizenSavingsTimeline> {
  const search = new URLSearchParams();
  if (params.dateStart) search.set("start_date", params.dateStart);
  if (params.dateEnd) search.set("end_date", params.dateEnd);
  const query = search.toString();
  const envelope = await httpGet<ApiEnvelope<KaizenSavingsTimeline>>(
    `${API_BASE}/${id}/savings-timeline${query ? `?${query}` : ""}`,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao calcular ganhos por período.");
}

// ---------------------------------------------------------------- evidências

export async function fetchKaizenEvidences(id: string): Promise<KaizenEvidence[]> {
  const envelope = await httpGet<ApiEnvelope<{ items: KaizenEvidence[] }>>(
    `${API_BASE}/${id}/evidences`,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao listar evidências.").items;
}

export async function uploadKaizenEvidence(
  id: string,
  params: {
    file?: File;
    stage: KaizenEvidenceStage;
    type: KaizenEvidenceType;
    description?: string;
    externalUrl?: string;
    revisionId?: string;
  },
): Promise<KaizenEvidence> {
  const form = new FormData();
  form.set("stage", params.stage);
  form.set("evidence_type", params.type);
  if (params.description) form.set("description", params.description);
  if (params.revisionId) form.set("revision_id", params.revisionId);
  if (params.type === "link") {
    form.set("external_url", params.externalUrl ?? "");
  } else if (params.file) {
    form.set("file", params.file);
  }
  const envelope = await httpPostForm<ApiEnvelope<KaizenEvidence>>(
    `${API_BASE}/${id}/evidences`,
    form,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao anexar evidência.");
}

export async function updateKaizenEvidence(
  id: string,
  evidenceId: string,
  payload: { stage?: KaizenEvidenceStage; description?: string },
): Promise<KaizenEvidence> {
  const envelope = await httpPatch<ApiEnvelope<KaizenEvidence>>(
    `${API_BASE}/${id}/evidences/${evidenceId}`,
    payload,
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao atualizar evidência.");
}

export async function deleteKaizenEvidence(id: string, evidenceId: string): Promise<void> {
  const envelope = await httpDelete<ApiEnvelope<{ id: string; deleted: boolean }>>(
    `${API_BASE}/${id}/evidences/${evidenceId}`,
  );
  unwrapApiDelpiEnvelope(envelope, "Erro ao excluir evidência.");
}

export function kaizenEvidenceFileUrl(id: string, evidenceId: string): string {
  return `${API_BASE}/${id}/evidences/${evidenceId}/file`;
}

export async function fetchKaizenEvidenceObjectUrl(
  id: string,
  evidenceId: string,
): Promise<string> {
  const response = await fetch(kaizenEvidenceFileUrl(id, evidenceId), {
    headers: authBearerHeader(),
  });
  if (!response.ok) {
    throw new Error("Erro ao carregar arquivo da evidência.");
  }
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}
