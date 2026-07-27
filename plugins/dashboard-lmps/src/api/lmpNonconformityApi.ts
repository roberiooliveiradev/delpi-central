import { httpDelete, httpGet, httpPost, httpPut } from "./httpClient";
import {
  unwrapApiDelpiEnvelope,
  type ApiSuccessResponse,
} from "../types/lmp";
import type {
  ImportLmpNonconformitiesResult,
  LmpNcHistoryListResponse,
  LmpNonconformity,
  LmpNonconformityExportFile,
  LmpNonconformityListResponse,
  LmpNonconformityPayload,
  LmpNonconformityStreak,
  LmpProblemTagListResponse,
} from "../types/lmpNonconformity";

const API_BASE = "/apps/api-delpi/engineering/lmps/nonconformities";

export type ListLmpNcParams = {
  status?: string;
  sale_number?: string;
  lmp_number?: string;
  customer_name?: string;
  product_code?: string;
  problem_tag?: string;
  start_date?: string;
  end_date?: string;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
  page?: number;
  page_size?: number;
};

function buildQuery(params: ListLmpNcParams): string {
  const search = new URLSearchParams();
  if (params.status) search.set("status", params.status);
  if (params.sale_number) search.set("sale_number", params.sale_number);
  if (params.lmp_number) search.set("lmp_number", params.lmp_number);
  if (params.customer_name) search.set("customer_name", params.customer_name);
  if (params.product_code) search.set("product_code", params.product_code);
  if (params.problem_tag) search.set("problem_tag", params.problem_tag);
  if (params.start_date) search.set("start_date", params.start_date);
  if (params.end_date) search.set("end_date", params.end_date);
  if (params.sort_by) search.set("sort_by", params.sort_by);
  if (params.sort_dir) search.set("sort_dir", params.sort_dir);
  if (params.page) search.set("page", String(params.page));
  if (params.page_size) search.set("page_size", String(params.page_size));
  const query = search.toString();
  return query ? `?${query}` : "";
}

export async function fetchLmpNonconformityStreak(): Promise<LmpNonconformityStreak> {
  const response = await httpGet<ApiSuccessResponse<LmpNonconformityStreak>>(
    `${API_BASE}/streak`,
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao carregar dias sem NC");
}

export async function fetchLmpProblemTags(): Promise<LmpProblemTagListResponse> {
  const response = await httpGet<ApiSuccessResponse<LmpProblemTagListResponse>>(
    `${API_BASE}/problem-tags`,
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao carregar tags de problema");
}

export async function fetchLmpNonconformities(
  params: ListLmpNcParams = {},
): Promise<LmpNonconformityListResponse> {
  const response = await httpGet<ApiSuccessResponse<LmpNonconformityListResponse>>(
    `${API_BASE}${buildQuery(params)}`,
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao listar não conformidades");
}

export async function fetchLmpNonconformity(id: string): Promise<LmpNonconformity> {
  const response = await httpGet<ApiSuccessResponse<LmpNonconformity>>(
    `${API_BASE}/${encodeURIComponent(id)}`,
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao carregar não conformidade");
}

export async function fetchLmpNonconformityHistory(
  id: string,
): Promise<LmpNcHistoryListResponse> {
  const response = await httpGet<ApiSuccessResponse<LmpNcHistoryListResponse>>(
    `${API_BASE}/${encodeURIComponent(id)}/history`,
  );
  return unwrapApiDelpiEnvelope(
    response,
    "Erro ao carregar histórico da não conformidade",
  );
}

export async function createLmpNonconformity(
  payload: LmpNonconformityPayload,
): Promise<LmpNonconformity> {
  const response = await httpPost<ApiSuccessResponse<LmpNonconformity>>(
    API_BASE,
    payload,
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao criar não conformidade");
}

export async function updateLmpNonconformity(
  id: string,
  payload: LmpNonconformityPayload,
): Promise<LmpNonconformity> {
  const response = await httpPut<ApiSuccessResponse<LmpNonconformity>>(
    `${API_BASE}/${encodeURIComponent(id)}`,
    payload,
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao atualizar não conformidade");
}

export async function deleteLmpNonconformity(id: string): Promise<void> {
  const response = await httpDelete<ApiSuccessResponse<{ id: string; deleted: boolean }>>(
    `${API_BASE}/${encodeURIComponent(id)}`,
  );
  unwrapApiDelpiEnvelope(response, "Erro ao excluir não conformidade");
}

export async function exportLmpNonconformities(): Promise<LmpNonconformityExportFile> {
  const response = await httpGet<ApiSuccessResponse<LmpNonconformityExportFile>>(
    `${API_BASE}/export`,
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao exportar não conformidades");
}

export async function importLmpNonconformities(
  items: Array<Record<string, unknown>>,
  options: { dryRun?: boolean } = {},
): Promise<ImportLmpNonconformitiesResult> {
  const response = await httpPost<ApiSuccessResponse<ImportLmpNonconformitiesResult>>(
    `${API_BASE}/import`,
    {
      items,
      dry_run: options.dryRun ?? false,
    },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao importar não conformidades");
}
