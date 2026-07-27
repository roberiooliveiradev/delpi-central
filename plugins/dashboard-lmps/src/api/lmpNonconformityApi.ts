import { httpDelete, httpGet, httpPost, httpPut } from "./httpClient";
import {
  unwrapApiDelpiEnvelope,
  type ApiSuccessResponse,
} from "../types/lmp";
import type {
  LmpNonconformity,
  LmpNonconformityListResponse,
  LmpNonconformityPayload,
} from "../types/lmpNonconformity";

const API_BASE = "/apps/api-delpi/engineering/lmps/nonconformities";

export type ListLmpNcParams = {
  status?: string;
  branch?: string;
  sale_number?: string;
  material_code?: string;
  product_code?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
};

function buildQuery(params: ListLmpNcParams): string {
  const search = new URLSearchParams();
  if (params.status) search.set("status", params.status);
  if (params.branch) search.set("branch", params.branch);
  if (params.sale_number) search.set("sale_number", params.sale_number);
  if (params.material_code) search.set("material_code", params.material_code);
  if (params.product_code) search.set("product_code", params.product_code);
  if (params.start_date) search.set("start_date", params.start_date);
  if (params.end_date) search.set("end_date", params.end_date);
  if (params.page) search.set("page", String(params.page));
  if (params.page_size) search.set("page_size", String(params.page_size));
  const query = search.toString();
  return query ? `?${query}` : "";
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
