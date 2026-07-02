import { httpGet } from "./httpClient";
import { unwrapApiDelpiEnvelope } from "../types/api";
import type {
  DespesasFiltrosData,
  DespesasLancamentosData,
  DespesasQueryFilters,
  DespesasRankingCentrosData,
  DespesasRankingFornecedoresData,
  DespesasResumoData,
  DespesasSerieData,
  LancamentosQueryParams,
} from "../types/despesasCentroCusto";
import {
  buildFiltrosQuery,
  buildLancamentosQuery,
  buildRankingCentrosQuery,
  buildRankingFornecedoresQuery,
  buildResumoQuery,
  buildSerieQuery,
  queryString,
} from "../utils/queryParams";

const API_BASE = "/apps/api-delpi/financeiro/despesas-centro-custo";

type RequestOptions = {
  signal?: AbortSignal;
};

async function getEnvelope<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const payload = await httpGet<unknown>(`${API_BASE}${path}`, options);
  return unwrapApiDelpiEnvelope<T>(payload);
}

export async function fetchDespesasFiltros(
  filters: DespesasQueryFilters,
  options: RequestOptions = {},
): Promise<DespesasFiltrosData> {
  return getEnvelope<DespesasFiltrosData>(
    `/filtros${queryString(buildFiltrosQuery(filters))}`,
    options,
  );
}

export async function fetchDespesasResumo(
  filters: DespesasQueryFilters,
  options: RequestOptions = {},
): Promise<DespesasResumoData> {
  return getEnvelope<DespesasResumoData>(
    `/resumo${queryString(buildResumoQuery(filters))}`,
    options,
  );
}

export async function fetchDespesasSerie(
  filters: DespesasQueryFilters,
  options: RequestOptions = {},
): Promise<DespesasSerieData> {
  return getEnvelope<DespesasSerieData>(
    `/serie${queryString(buildSerieQuery(filters))}`,
    options,
  );
}

export async function fetchDespesasRankingCentros(
  filters: DespesasQueryFilters,
  limit = 10,
  options: RequestOptions = {},
): Promise<DespesasRankingCentrosData> {
  return getEnvelope<DespesasRankingCentrosData>(
    `/ranking-centros${queryString(buildRankingCentrosQuery(filters, limit))}`,
    options,
  );
}

export async function fetchDespesasRankingFornecedores(
  filters: DespesasQueryFilters,
  limit = 10,
  options: RequestOptions = {},
): Promise<DespesasRankingFornecedoresData> {
  return getEnvelope<DespesasRankingFornecedoresData>(
    `/ranking-fornecedores${queryString(buildRankingFornecedoresQuery(filters, limit))}`,
    options,
  );
}

export async function fetchDespesasLancamentos(
  params: LancamentosQueryParams,
  options: RequestOptions = {},
): Promise<DespesasLancamentosData> {
  return getEnvelope<DespesasLancamentosData>(
    `/lancamentos${queryString(buildLancamentosQuery(params))}`,
    options,
  );
}

export const despesasCentroCustoApiPaths = {
  filtros: `${API_BASE}/filtros`,
  resumo: `${API_BASE}/resumo`,
  serie: `${API_BASE}/serie`,
  rankingCentros: `${API_BASE}/ranking-centros`,
  rankingFornecedores: `${API_BASE}/ranking-fornecedores`,
  lancamentos: `${API_BASE}/lancamentos`,
} as const;
