import {
  httpDelete,
  httpGet,
  httpPost,
  httpPut,
  unwrapApiDelpiEnvelope,
  type ApiEnvelope,
} from "./httpClient";
import type { KaizenListResponse, KaizenRecord } from "../types/kaizen";

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

export type ImportKaizensFromSheetResult = {
  created: number;
  skipped: number;
  errors: number;
  items: Array<Record<string, unknown>>;
};

export async function importKaizensFromSheet(
  dryRun = false,
): Promise<ImportKaizensFromSheetResult> {
  const envelope = await httpPost<ApiEnvelope<ImportKaizensFromSheetResult>>(
    `${API_BASE}/import-from-sheet`,
    { dry_run: dryRun },
  );
  return unwrapApiDelpiEnvelope(envelope, "Erro ao importar kaizens da planilha.");
}
