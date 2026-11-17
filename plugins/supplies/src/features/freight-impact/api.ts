import { httpGet, suppliesApiUrl } from "../../api/httpClient";

/** Mesma precisão decimal (2 casas) do Portal Financeiro. */
export type Money = string;
export type FreightSituation = "normal" | "above_limit" | "inconsistent";
export type FreightFilterSituation = FreightSituation | "all";
export type FreightDateMode = "issue" | "entry";

export type FreightImpactFilters = {
  branches: string[];
  dateFrom: string;
  dateTo: string;
  dateMode: FreightDateMode;
  situation: FreightFilterSituation;
  page: number;
};

export type FreightAllocation = {
  freight_document: string;
  freight_series: string;
  carrier_code: string;
  carrier_store: string;
  carrier_name: string;
  freight_issue_date: string;
  freight_access_key: string;
  freight_gross_value: Money;
  allocation_base: Money;
  allocated_value: Money;
  linked_invoice_count: number;
};

export type FreightImpactInvoice = {
  branch: string;
  invoice_document: string;
  invoice_series: string;
  supplier_code: string;
  supplier_store: string;
  supplier_name: string;
  issue_date: string;
  entry_date: string;
  goods_value: Money;
  freight_total: Money;
  freight_pct: Money | null;
  freight_limit: Money | null;
  situation: FreightSituation;
  reason_codes: string[];
  cte_count: number;
  allocations: FreightAllocation[];
};

export type FreightImpactResponse = {
  source: "financial_purchase_freight_links";
  method: "financial_freight_allocation_v1";
  scope: "purchase_invoices_with_freight_links";
  limits: Record<string, Money>;
  reason_labels: Record<string, string>;
  summary: {
    invoice_count: number;
    linked_invoice_count: number;
    inconsistent_count: number;
    above_limit_count: number;
    purchases_total: Money;
    freight_total: Money;
    freight_pct: Money | null;
  };
  monthly: Array<{
    period: string;
    purchase_cost: Money;
    freight_cost: Money;
    freight_pct: Money | null;
    invoices: number;
  }>;
  items: FreightImpactInvoice[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  is_complete: boolean;
};

export function buildFreightImpactParams(filters: FreightImpactFilters): URLSearchParams {
  const params = new URLSearchParams();
  for (const code of [...new Set(filters.branches)]) {
    if (code === "01" || code === "02") params.append("branch", code);
  }
  params.set("date_from", filters.dateFrom);
  params.set("date_to", filters.dateTo);
  params.set("date_mode", filters.dateMode);
  params.set("situation", filters.situation);
  params.set("page", String(filters.page));
  params.set("page_size", "25");
  return params;
}

export function getFreightImpact(filters: FreightImpactFilters, signal?: AbortSignal): Promise<FreightImpactResponse> {
  return httpGet<FreightImpactResponse>(
    suppliesApiUrl(`/analytics/freight-impact?${buildFreightImpactParams(filters)}`),
    { signal },
  );
}
