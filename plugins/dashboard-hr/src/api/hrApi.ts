import { httpGet } from "./httpClient";
import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import type { HrBranchesResponse, HrFilterParams, HrSnapshot } from "../types/hr";

export const HR_API_BASE = "/apps/api-delpi/hr";

function buildQuery(params: HrFilterParams = {}): string {
  const searchParams = new URLSearchParams();

  if (params.start_date) searchParams.set("start_date", params.start_date);
  if (params.end_date) searchParams.set("end_date", params.end_date);
  if (params.branch) searchParams.set("branch", params.branch);

  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

async function fetchHrData<T>(
  path: string,
  params: HrFilterParams = {},
  signal?: AbortSignal
): Promise<T> {
  const response = await httpGet<ApiSuccessResponse<T>>(
    `${HR_API_BASE}${path}${buildQuery(params)}`,
    { signal }
  );

  return unwrapApiDelpiEnvelope(response, "Erro na API de RH");
}

export function getHrSnapshot(params: HrFilterParams = {}, signal?: AbortSignal) {
  return fetchHrData<HrSnapshot>("/snapshot", params, signal);
}

export function getHrBranches(signal?: AbortSignal) {
  return fetchHrData<HrBranchesResponse>("/branches", {}, signal);
}
