import { unwrapApiDelpiEnvelope, type ApiSuccessResponse } from "../types/api";
import type {
  UnproductiveHoursItemsData,
  UnproductiveHoursItemsFilters,
  UnproductiveHoursQueryFilters,
  UnproductiveHoursRankingData,
  UnproductiveHoursRankingFilters,
  UnproductiveHoursSummaryData,
} from "../types/unproductiveHours";
import { UNPRODUCTIVE_HOURS_PAGE_SIZE, UNPRODUCTIVE_HOURS_RANKING_LIMIT } from "../types/unproductiveHours";
import { httpGet } from "./httpClient";

export const UNPRODUCTIVE_HOURS_API_BASE = "/apps/api-delpi/production/unproductive-hours";

type RequestOptions = { signal?: AbortSignal };

function appendOptional(params: URLSearchParams, key: string, value: string | undefined): void {
  const trimmed = value?.trim();
  if (trimmed) params.set(key, trimmed);
}

function buildBaseQuery(filters: UnproductiveHoursQueryFilters): URLSearchParams {
  const params = new URLSearchParams();
  params.set("start_date", filters.start_date);
  params.set("end_date", filters.end_date);
  if (filters.branch) params.set("branch", filters.branch);
  appendOptional(params, "stop_reason", filters.stop_reason);
  appendOptional(params, "resource", filters.resource);
  appendOptional(params, "cost_center", filters.cost_center);
  appendOptional(params, "operator_code", filters.operator_code);
  return params;
}

async function getEnvelope<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await httpGet<ApiSuccessResponse<T>>(`${UNPRODUCTIVE_HOURS_API_BASE}${path}`, options);
  return unwrapApiDelpiEnvelope(response, "Erro ao carregar horas improdutivas");
}

export async function getUnproductiveHoursSummary(
  filters: UnproductiveHoursQueryFilters,
  options: RequestOptions = {},
): Promise<UnproductiveHoursSummaryData> {
  const query = buildBaseQuery(filters);
  return getEnvelope<UnproductiveHoursSummaryData>(`/summary?${query.toString()}`, options);
}

export async function getUnproductiveHoursItems(
  filters: UnproductiveHoursItemsFilters,
  options: RequestOptions = {},
): Promise<UnproductiveHoursItemsData> {
  const query = buildBaseQuery(filters);
  query.set("page", String(filters.page));
  query.set("page_size", String(filters.page_size ?? UNPRODUCTIVE_HOURS_PAGE_SIZE));
  if (filters.sort) query.set("sort", filters.sort);
  return getEnvelope<UnproductiveHoursItemsData>(`/items?${query.toString()}`, options);
}

export async function getUnproductiveHoursRanking(
  filters: UnproductiveHoursRankingFilters,
  options: RequestOptions = {},
): Promise<UnproductiveHoursRankingData> {
  const query = buildBaseQuery(filters);
  query.set("rank_by", filters.rank_by);
  query.set("metric", filters.metric ?? "hours");
  query.set("limit", String(filters.limit ?? UNPRODUCTIVE_HOURS_RANKING_LIMIT));
  return getEnvelope<UnproductiveHoursRankingData>(`/ranking?${query.toString()}`, options);
}

/** Busca todas as páginas de items para exportação. */
export async function fetchAllUnproductiveHoursItems(
  filters: UnproductiveHoursQueryFilters,
  options: RequestOptions = {},
): Promise<UnproductiveHoursItemsData["items"]> {
  const pageSize = UNPRODUCTIVE_HOURS_PAGE_SIZE;
  const first = await getUnproductiveHoursItems(
    { ...filters, page: 1, page_size: pageSize, sort: "date_desc" },
    options,
  );
  const items = [...(first.items ?? [])];
  const total = first.pagination?.total ?? first.total ?? items.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  for (let page = 2; page <= totalPages; page += 1) {
    if (options.signal?.aborted) break;
    const next = await getUnproductiveHoursItems(
      { ...filters, page, page_size: pageSize, sort: "date_desc" },
      options,
    );
    items.push(...(next.items ?? []));
  }

  return items;
}
