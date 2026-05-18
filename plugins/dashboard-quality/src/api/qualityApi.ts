import { httpGet } from "./httpClient";
import { buildQuery } from "./query";
import type { ApiSuccessResponse } from "../types/api";

const API_BASE = "/apps/api-delpi/quality";

export type DateRangeParams = {
  branch?: string;
  date_start?: string;
  date_end?: string;
};

export async function getPpmInternalSummary(
  params: DateRangeParams = {},
  signal?: AbortSignal
): Promise<unknown> {
  const query = buildQuery(params);

  const response = await httpGet<ApiSuccessResponse<unknown>>(
    `${API_BASE}/ppm/internal/summary${query}`,
    { signal }
  );

  return response.data;
}
