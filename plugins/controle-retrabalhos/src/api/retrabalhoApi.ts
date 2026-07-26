import { httpGet } from "./httpClient";
import { unwrapApiDelpiEnvelope } from "../types/api";
import type {
  RetrabalhoColaboradorItem,
  RetrabalhoDetalhesData,
  RetrabalhoMensalData,
  RetrabalhoQueryFilters,
  RetrabalhoResumo,
  RetrabalhoRecursoItem,
} from "../types/retrabalho";
import { queryString } from "../utils/queryParams";

const API_BASE = "/apps/api-delpi/retrabalhos";

type RequestOptions = { signal?: AbortSignal };

async function getEnvelope<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const payload = await httpGet<unknown>(`${API_BASE}${path}`, options);
  return unwrapApiDelpiEnvelope<T>(payload);
}

function baseQuery(filters: RetrabalhoQueryFilters) {
  return {
    filial: filters.filial,
    start_date: filters.start_date,
    end_date: filters.end_date,
  };
}

export async function fetchRetrabalhoResumo(
  filters: RetrabalhoQueryFilters,
  options: RequestOptions = {},
): Promise<RetrabalhoResumo> {
  return getEnvelope<RetrabalhoResumo>(`/resumo${queryString(baseQuery(filters))}`, options);
}

export async function fetchRetrabalhoMensal(
  filters: RetrabalhoQueryFilters,
  options: RequestOptions = {},
): Promise<RetrabalhoMensalData> {
  return getEnvelope<RetrabalhoMensalData>(`/mensal${queryString(baseQuery(filters))}`, options);
}

export async function fetchRetrabalhoRecursos(
  filters: RetrabalhoQueryFilters,
  limit = 10,
  options: RequestOptions = {},
): Promise<{ items: RetrabalhoRecursoItem[] }> {
  const data = await getEnvelope<{ items: RetrabalhoRecursoItem[] }>(
    `/recursos${queryString({ ...baseQuery(filters), limit })}`,
    options,
  );
  return data;
}

export async function fetchRetrabalhoColaboradores(
  filters: RetrabalhoQueryFilters,
  limit = 10,
  options: RequestOptions = {},
): Promise<{ items: RetrabalhoColaboradorItem[] }> {
  const data = await getEnvelope<{ items: RetrabalhoColaboradorItem[] }>(
    `/colaboradores${queryString({ ...baseQuery(filters), limit })}`,
    options,
  );
  return data;
}

export async function fetchRetrabalhoDetalhes(
  filters: RetrabalhoQueryFilters,
  page: number,
  pageSize: number,
  options: RequestOptions = {},
): Promise<RetrabalhoDetalhesData> {
  return getEnvelope<RetrabalhoDetalhesData>(
    `/detalhes${queryString({ ...baseQuery(filters), page, pageSize })}`,
    options,
  );
}
