import { httpGet } from "./httpClient";
import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import type {
  EngineeringFilterParams,
  TransformaProcessesList,
  TransformaSummary,
} from "../types/engineering";
import type {
  LmpsDashboardParams,
  LmpsDashboardResponse,
  LmpsDashboardSummary,
  LmpsDashboardCharts,
} from "../types/lmp";
import { inputDateToLmpApi } from "../utils/lmpDates";

export const ENGINEERING_API_BASE = "/apps/api-delpi/engineering";

function buildLmpQuery(params: LmpsDashboardParams = {}): string {
  const searchParams = new URLSearchParams();

  const dateStart = inputDateToLmpApi(params.start_date);
  const dateEnd = inputDateToLmpApi(params.end_date);

  if (dateStart) searchParams.set("start_date", dateStart);
  if (dateEnd) searchParams.set("end_date", dateEnd);
  if (params.branch) searchParams.set("branch", params.branch);
  if (params.listing_type && params.listing_type !== "Todos") {
    searchParams.set("listing_type", params.listing_type);
  }
  if (params.status && params.status !== "Todos") {
    searchParams.set("status", params.status);
  }
  if (params.page) searchParams.set("page", String(params.page));
  if (params.page_size) searchParams.set("page_size", String(params.page_size));
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

function buildQuery(params: EngineeringFilterParams = {}): string {
  const searchParams = new URLSearchParams();

  if (params.start_date) searchParams.set("start_date", params.start_date);
  if (params.end_date) searchParams.set("end_date", params.end_date);
  if (params.filial_id) searchParams.set("filial_id", params.filial_id);
  if (params.branch) searchParams.set("filial_id", params.branch);
  if (params.name_process) searchParams.set("name_process", params.name_process);
  if (params.sector_name) searchParams.set("sector_name", params.sector_name);
  if (params.status) searchParams.set("status", params.status);

  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

async function fetchEngineeringData<T>(
  path: string,
  params: EngineeringFilterParams = {},
  signal?: AbortSignal
): Promise<T> {
  const response = await httpGet<ApiSuccessResponse<T>>(
    `${ENGINEERING_API_BASE}${path}${buildQuery(params)}`,
    { signal }
  );

  return unwrapApiDelpiEnvelope(response, "Erro na API de engenharia");
}

export function getTransformaSummary(
  params: Pick<EngineeringFilterParams, "start_date" | "end_date" | "filial_id" | "branch">,
  signal?: AbortSignal
) {
  return fetchEngineeringData<TransformaSummary>(
    "/transforma-mais/processes/summary",
    params,
    signal
  );
}

export function getTransformaProcesses(
  params: EngineeringFilterParams = {},
  signal?: AbortSignal
) {
  return fetchEngineeringData<TransformaProcessesList>(
    "/transforma-mais/processes",
    params,
    signal
  );
}

export async function getLmpsDashboard(
  params: LmpsDashboardParams,
  signal?: AbortSignal
): Promise<LmpsDashboardResponse> {
  const response = await httpGet<ApiSuccessResponse<LmpsDashboardResponse>>(
    `${ENGINEERING_API_BASE}/lmps/dashboard${buildLmpQuery(params)}`,
    { signal }
  );

  return unwrapApiDelpiEnvelope(response, "Erro ao carregar LMPs");
}

export async function getLmpsDashboardSummary(
  params: Omit<LmpsDashboardParams, "page" | "page_size">,
  signal?: AbortSignal,
): Promise<LmpsDashboardSummary> {
  const response = await httpGet<ApiSuccessResponse<LmpsDashboardSummary>>(
    `${ENGINEERING_API_BASE}/lmps/dashboard/summary${buildLmpQuery(params)}`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao carregar KPIs de LMPs");
}

export async function getLmpsDashboardCharts(
  params: Omit<LmpsDashboardParams, "page" | "page_size">,
  signal?: AbortSignal,
): Promise<LmpsDashboardCharts> {
  const response = await httpGet<ApiSuccessResponse<LmpsDashboardCharts>>(
    `${ENGINEERING_API_BASE}/lmps/dashboard/charts${buildLmpQuery(params)}`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao carregar gráficos de LMPs");
}

export type LmpsDashboardItemsResponse = {
  items: LmpsDashboardResponse["items"];
  total: number;
  page: number;
  page_size: number;
};

export async function getLmpsDashboardItems(
  params: LmpsDashboardParams,
  signal?: AbortSignal,
): Promise<LmpsDashboardItemsResponse> {
  const response = await httpGet<ApiSuccessResponse<LmpsDashboardItemsResponse>>(
    `${ENGINEERING_API_BASE}/lmps/dashboard/items${buildLmpQuery(params)}`,
    { signal },
  );
  return unwrapApiDelpiEnvelope(response, "Erro ao carregar itens de LMPs");
}
