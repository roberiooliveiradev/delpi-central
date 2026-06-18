import type { FetchHistoricoParams, HistoricoFilters } from "../types/inspecoesEntradaHistorico";

export const EMPTY_HISTORICO_FILTERS: HistoricoFilters = {
  result: "",
  date_from: "",
  date_to: "",
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
  if (filters.date_from.trim()) params.date_from = filters.date_from.trim();
  if (filters.date_to.trim()) params.date_to = filters.date_to.trim();
  if (filters.supplier.trim()) params.supplier = filters.supplier.trim();
  if (filters.product_code.trim()) params.product_code = filters.product_code.trim();
  if (filters.inspector.trim()) params.inspector = filters.inspector.trim();
  if (filters.invoice_number.trim()) params.invoice_number = filters.invoice_number.trim();
  if (filters.lot.trim()) params.lot = filters.lot.trim();

  return params;
}
