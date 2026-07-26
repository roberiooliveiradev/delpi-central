import type { FetchHistoricoParams, HistoricoFilters } from "../types/inspecoesEntradaHistorico";

export const EMPTY_HISTORICO_FILTERS: HistoricoFilters = {
  result: "",
  start_date: "",
  end_date: "",
  supplier: "",
  product_code: "",
  inspector: "",
  invoice_number: "",
  lot: "",
};

export function hasActiveHistoricoFilters(filters: HistoricoFilters): boolean {
  return Object.values(filters).some((value) => value.trim() !== "");
}

export function filtersToFetchParams(
  branch: string,
  page: number,
  pageSize: number,
  filters: HistoricoFilters,
): FetchHistoricoParams {
  const params: FetchHistoricoParams = {
    branch,
    page,
    page_size: pageSize,
  };

  if (filters.result) params.result = filters.result;
  if (filters.start_date.trim()) params.start_date = filters.start_date.trim();
  if (filters.end_date.trim()) params.end_date = filters.end_date.trim();
  if (filters.supplier.trim()) params.supplier = filters.supplier.trim();
  if (filters.product_code.trim()) params.product_code = filters.product_code.trim();
  if (filters.inspector.trim()) params.inspector = filters.inspector.trim();
  if (filters.invoice_number.trim()) params.invoice_number = filters.invoice_number.trim();
  if (filters.lot.trim()) params.lot = filters.lot.trim();

  return params;
}
