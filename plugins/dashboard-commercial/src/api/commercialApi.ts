import { httpGet } from "./httpClient";
import type { ApiSuccessResponse } from "../types/api";
import type { ChartGranularity } from "../types/chart";
import type {
  ClosingRateData,
  CommercialFilterParams,
  CommercialRolSeriesData,
  NewClientsAverageData,
  NewClientsRolPctData,
  RolTargetData,
} from "../types/commercial";

export const COMMERCIAL_API_BASE = "/apps/api-delpi/commercial";

function buildQuery(
  params: CommercialFilterParams & { granularity?: ChartGranularity }
): string {
  const searchParams = new URLSearchParams();

  if (params.start_date) searchParams.set("start_date", params.start_date);
  if (params.end_date) searchParams.set("end_date", params.end_date);
  if (params.branch) searchParams.set("branch", params.branch);
  if (params.granularity) searchParams.set("granularity", params.granularity);

  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

async function fetchCommercialData<T>(
  path: string,
  params: CommercialFilterParams = {},
  signal?: AbortSignal
): Promise<T> {
  const response = await httpGet<ApiSuccessResponse<T>>(
    `${COMMERCIAL_API_BASE}${path}${buildQuery(params)}`,
    { signal }
  );

  if (response.success === false) {
    throw new Error(response.message || "Erro na API comercial");
  }

  return response.data;
}

export function getHeadOfficeRolTarget(
  params: Pick<CommercialFilterParams, "start_date" | "end_date">,
  signal?: AbortSignal
) {
  return fetchCommercialData<RolTargetData>(
    "/head_office_rol_target_pct",
    params,
    signal
  );
}

export function getBranchRolTarget(
  params: Pick<CommercialFilterParams, "start_date" | "end_date">,
  signal?: AbortSignal
) {
  return fetchCommercialData<RolTargetData>(
    "/branch_rol_target_pct",
    params,
    signal
  );
}

export function getClosingRate(
  params: CommercialFilterParams,
  signal?: AbortSignal
) {
  return fetchCommercialData<ClosingRateData>("/closing-rate", params, signal);
}

export function getNewClientsAverage(
  params: CommercialFilterParams,
  signal?: AbortSignal
) {
  return fetchCommercialData<NewClientsAverageData>(
    "/new-clients-average",
    params,
    signal
  );
}

export function getNewClientsRolPct(
  params: CommercialFilterParams,
  signal?: AbortSignal
) {
  return fetchCommercialData<NewClientsRolPctData>(
    "/new-clients-rol-pct",
    params,
    signal
  );
}

export function getCommercialRolSeries(
  params: Pick<CommercialFilterParams, "start_date" | "end_date"> & {
    granularity: ChartGranularity;
  },
  signal?: AbortSignal
) {
  return fetchCommercialData<CommercialRolSeriesData>(
    "/rol/series",
    params,
    signal
  );
}
