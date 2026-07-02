import type { DespesasQueryFilters, LancamentosQueryParams } from "../types/despesasCentroCusto";

function appendPeriodParams(params: URLSearchParams, filters: DespesasQueryFilters): void {
  params.set("start_date", filters.startDate);
  params.set("end_date", filters.endDate);
  if (filters.branch) {
    params.set("branch", filters.branch);
  }
}

function appendSupplierParams(params: URLSearchParams, filters: DespesasQueryFilters): void {
  if (filters.supplierCode) {
    params.set("supplier_code", filters.supplierCode);
  }
  if (filters.supplierStore) {
    params.set("supplier_store", filters.supplierStore);
  }
}

export function buildFiltrosQuery(filters: DespesasQueryFilters): URLSearchParams {
  const params = new URLSearchParams();
  appendPeriodParams(params, filters);
  if (filters.costCenter) {
    params.set("cost_center", filters.costCenter);
  }
  return params;
}

export function buildResumoQuery(filters: DespesasQueryFilters): URLSearchParams {
  const params = new URLSearchParams();
  appendPeriodParams(params, filters);
  if (filters.costCenter) {
    params.set("cost_center", filters.costCenter);
  }
  appendSupplierParams(params, filters);
  return params;
}

export function buildSerieQuery(filters: DespesasQueryFilters): URLSearchParams {
  return buildResumoQuery(filters);
}

export function buildRankingCentrosQuery(
  filters: DespesasQueryFilters,
  limit = 10,
): URLSearchParams {
  const params = new URLSearchParams();
  appendPeriodParams(params, filters);
  appendSupplierParams(params, filters);
  params.set("limit", String(limit));
  return params;
}

export function buildRankingFornecedoresQuery(
  filters: DespesasQueryFilters,
  limit = 10,
): URLSearchParams {
  const params = new URLSearchParams();
  appendPeriodParams(params, filters);
  if (filters.costCenter) {
    params.set("cost_center", filters.costCenter);
  }
  params.set("limit", String(limit));
  return params;
}

export function buildLancamentosQuery(paramsInput: LancamentosQueryParams): URLSearchParams {
  const params = buildResumoQuery(paramsInput);
  if (paramsInput.search?.trim()) {
    params.set("search", paramsInput.search.trim());
  }
  params.set("page", String(paramsInput.page ?? 1));
  params.set("page_size", String(paramsInput.pageSize ?? 50));
  if (paramsInput.sortBy) {
    params.set("sort_by", paramsInput.sortBy);
  }
  if (paramsInput.sortDir) {
    params.set("sort_dir", paramsInput.sortDir);
  }
  return params;
}

export function queryString(params: URLSearchParams): string {
  const value = params.toString();
  return value ? `?${value}` : "";
}
