import { httpGet } from "./httpClient";
import { unwrapApiDelpiEnvelope } from "../types/api";
import type {
  ScrapQueryFilters,
  ScrapRankingDimension,
  ScrapRankingsData,
  ScrapRegistrosData,
  ScrapResumo,
} from "../types/scrap";
import { queryString } from "../utils/queryParams";

const API_BASE = "/apps/api-delpi/refugos";

type RequestOptions = { signal?: AbortSignal };

async function getEnvelope<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const payload = await httpGet<unknown>(`${API_BASE}${path}`, options);
  return unwrapApiDelpiEnvelope<T>(payload);
}

function baseQuery(filters: ScrapQueryFilters) {
  return {
    filial: filters.filial,
    dataInicio: filters.dataInicio,
    dataFim: filters.dataFim,
  };
}

export async function fetchScrapResumo(
  filters: ScrapQueryFilters,
  options: RequestOptions = {},
): Promise<ScrapResumo> {
  return getEnvelope<ScrapResumo>(`/resumo${queryString(baseQuery(filters))}`, options);
}

export async function fetchScrapRankings(
  filters: ScrapQueryFilters,
  dimension: ScrapRankingDimension,
  limit = 10,
  options: RequestOptions = {},
): Promise<ScrapRankingsData> {
  return getEnvelope<ScrapRankingsData>(
    `/rankings${queryString({ ...baseQuery(filters), dimension, limit })}`,
    options,
  );
}

export async function fetchScrapRegistros(
  filters: ScrapQueryFilters,
  page: number,
  pageSize: number,
  options: RequestOptions = {},
): Promise<ScrapRegistrosData> {
  return getEnvelope<ScrapRegistrosData>(
    `/registros${queryString({ ...baseQuery(filters), page, pageSize })}`,
    options,
  );
}
