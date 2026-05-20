import { httpGet } from "./httpClient";
import type { ApiSuccessResponse } from "../types/api";
import type {
  EngineeringFilterParams,
  TransformaProcessesList,
  TransformaSummary,
} from "../types/engineering";

export const ENGINEERING_API_BASE = "/apps/api-delpi/engineering";

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

  if (response.success === false) {
    throw new Error(response.message || "Erro na API de engenharia");
  }

  return response.data;
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
