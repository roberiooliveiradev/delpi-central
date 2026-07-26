import { httpGet } from "./httpClient";
import { unwrapApiDelpiEnvelope } from "../types/api";
import type {
  ScrapFiltrosData,
  ScrapQueryFilters,
  ScrapRankingDimension,
  ScrapRankingsData,
  ScrapRegistrosData,
  ScrapResumo,
  ScrapSerieData,
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
    start_date: filters.start_date,
    end_date: filters.end_date,
    mp: filters.mp,
    pa: filters.pa,
    op: filters.op,
    motivo: filters.motivo,
    centroTrabalho: filters.centroTrabalho,
  };
}

function periodQuery(filters: Pick<ScrapQueryFilters, "filial" | "start_date" | "end_date">) {
  return {
    filial: filters.filial,
    start_date: filters.start_date,
    end_date: filters.end_date,
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

export async function fetchScrapSerie(
  filters: ScrapQueryFilters,
  granularity: "day" | "month" | "auto" = "auto",
  options: RequestOptions = {},
): Promise<ScrapSerieData> {
  return getEnvelope<ScrapSerieData>(
    `/serie${queryString({ ...baseQuery(filters), granularity })}`,
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

export async function fetchScrapFiltros(
  filters: Pick<ScrapQueryFilters, "filial" | "start_date" | "end_date">,
  options: RequestOptions = {},
): Promise<ScrapFiltrosData> {
  return getEnvelope<ScrapFiltrosData>(
    `/filtros${queryString(periodQuery(filters))}`,
    options,
  );
}
