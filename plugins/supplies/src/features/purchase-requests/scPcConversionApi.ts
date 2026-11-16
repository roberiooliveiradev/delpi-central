import { httpGet, suppliesApiUrl } from "../../api/httpClient";

export type ScPcConversionStatus =
  | "converted" | "pending" | "order_before_release" | "invalid_order_date";

export type ScPcConversionSummary = {
  approved_requests: number;
  with_approval: number;
  without_approval: number;
  converted_requests: number;
  pending_requests: number;
  before_release: number;
  invalid_order_dates: number;
  sum_conversion_days: number;
  avg_days: number | null;
  same_day: number;
  one_to_two_days: number;
  three_to_five_days: number;
  six_to_ten_days: number;
  over_ten_days: number;
};

export type ScPcConversionItem = {
  branch: string;
  request_number: string;
  issue_date: string | null;
  final_approval_date: string | null;
  effective_start_date: string;
  start_date_source: "approval_release" | "issue_without_approval";
  first_order_date: string | null;
  first_order_number: string | null;
  linked_order_count: number;
  approval_levels: number;
  item_count: number;
  conversion_status: ScPcConversionStatus;
  conversion_days: number | null;
};

export type ScPcConversionResponse = {
  source: "SC1010+SCR010+SC7010";
  scope: "release_or_issue_without_approval_to_first_order";
  period_anchor: "effective_start_date";
  unit: "calendar_days";
  summary: ScPcConversionSummary;
  branch_breakdown: Record<string, ScPcConversionSummary>;
  items: ScPcConversionItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type ScPcConversionFilters = {
  branches: string[];
  dateFrom: string;
  dateTo: string;
  requestNumber: string;
  page: number;
};

export function buildScPcConversionParams(filters: ScPcConversionFilters): URLSearchParams {
  const params = new URLSearchParams();
  for (const branch of filters.branches) {
    if (branch === "01" || branch === "02") params.append("branch", branch);
  }
  params.set("date_from", filters.dateFrom);
  params.set("date_to", filters.dateTo);
  if (filters.requestNumber.trim()) params.set("request_number", filters.requestNumber.trim());
  params.set("page", String(filters.page));
  params.set("page_size", "25");
  return params;
}

export function getScPcConversion(
  filters: ScPcConversionFilters,
  signal?: AbortSignal,
): Promise<ScPcConversionResponse> {
  return httpGet<ScPcConversionResponse>(
    suppliesApiUrl("/purchase-requests/sc-pc-conversion?" + buildScPcConversionParams(filters).toString()),
    { signal },
  );
}
