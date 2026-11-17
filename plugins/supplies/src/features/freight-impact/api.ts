import { httpGet, suppliesApiUrl } from "../../api/httpClient";

export type FreightImpactFilters = { branches: string[]; dateFrom: string; dateTo: string; page: number };
export type FreightImpactInvoice = {
  branch: string; invoice_document: string; invoice_series: string;
  supplier_code: string; supplier_store: string; supplier_name: string;
  issue_date: string; purchase_cost: number; freight_cost: number;
  cte_count: number; freight_pct: number | null; calculation_status: string;
};
export type FreightImpactResponse = {
  source: string; method: string; scope: string;
  summary: { invoice_count: number; valid_invoice_count: number; invalid_base_count: number;
    with_freight_count: number; without_freight_count: number; purchases_total: number;
    freight_total: number; freight_pct: number | null };
  monthly: Array<{period: string; purchase_cost: number; freight_cost: number; freight_pct: number | null; invoices: number}>;
  items: FreightImpactInvoice[]; total: number; page: number; page_size: number; total_pages: number;
};
export function buildFreightImpactParams(filters: FreightImpactFilters): URLSearchParams {
  const params = new URLSearchParams();
  for (const code of [...new Set(filters.branches)]) {
    if (code === "01" || code === "02") params.append("branch", code);
  }
  params.set("date_from", filters.dateFrom);
  params.set("date_to", filters.dateTo);
  params.set("page", String(filters.page));
  params.set("page_size", "25");
  return params;
}
export function getFreightImpact(filters: FreightImpactFilters, signal?: AbortSignal): Promise<FreightImpactResponse> {
  return httpGet<FreightImpactResponse>(suppliesApiUrl(`/analytics/freight-impact?${buildFreightImpactParams(filters)}`), { signal });
}
