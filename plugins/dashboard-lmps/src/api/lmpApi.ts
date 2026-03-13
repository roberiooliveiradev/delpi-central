import { httpGet } from "./httpClient";
import type { ApiSuccessResponse, ListLmpsParams, LmpItem, Page } from "../types/lmp";

function buildQuery(params: ListLmpsParams): string {
  const searchParams = new URLSearchParams();

  if (params.date_start) searchParams.set("date_start", params.date_start);
  if (params.date_end) searchParams.set("date_end", params.date_end);
  if (params.page) searchParams.set("page", String(params.page));
  if (params.page_size) searchParams.set("page_size", String(params.page_size));

  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export async function listLmps(
  params: ListLmpsParams,
  token?: string,
  signal?: AbortSignal
): Promise<Page<LmpItem>> {
  const query = buildQuery(params);

  const response = await httpGet<ApiSuccessResponse<Page<LmpItem>>>(
    `/apps/api-delpi/lmps/${query}`,
    { token, signal }
  );

  return response.data;
}