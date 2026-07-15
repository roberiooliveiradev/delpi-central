import { httpGet } from "./httpClient";
import { unwrapApiDelpiEnvelope } from "../types/api";
import type {
  ScrapFiltrosData,
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
    mp: filters.mp,
    pa: filters.pa,
    op: filters.op,
    motivo: filters.motivo,
    centroTrabalho: filters.centroTrabalho,
  };
}

function periodQuery(filters: Pick<ScrapQueryFilters, "filial" | "dataInicio" | "dataFim">) {
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

export async function fetchScrapFiltros(
  filters: Pick<ScrapQueryFilters, "filial" | "dataInicio" | "dataFim">,
  options: RequestOptions = {},
): Promise<ScrapFiltrosData> {
  return getEnvelope<ScrapFiltrosData>(
    `/filtros${queryString(periodQuery(filters))}`,
    options,
  );
}
