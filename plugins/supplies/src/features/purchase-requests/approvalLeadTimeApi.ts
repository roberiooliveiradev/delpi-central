import { httpGet, suppliesApiUrl } from "../../api/httpClient";

export type ApprovalLeadTimeEvent = {
  level: string;
  approved_at: string;
  action_user_code: string;
  approver_code: string;
};

export type ApprovalLeadTimeRecord = {
  branch: string;
  request_number: string;
  issue_date: string;
  requester_name: string | null;
  requester_user_id: string | null;
  item_count: number;
  final_approval_date: string;
  approval_levels: number;
  lead_days: number;
  events: ApprovalLeadTimeEvent[];
};

export type ApprovalLeadTimeResponse = {
  source: "SCR010";
  scope: "confirmed_history_only";
  unit: "calendar_days";
  filters: {
    branches: string[];
    date_from: string;
    date_to: string;
    request_number: string | null;
  };
  summary: {
    total_requests: number;
    avg_lead_days: number | null;
    same_day: number;
    one_to_two_days: number;
    three_to_five_days: number;
    six_to_ten_days: number;
    over_10_days: number;
    multi_level: number;
  };
  items: ApprovalLeadTimeRecord[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type ApprovalLeadTimeFilters = {
  branches: string[];
  dateFrom: string;
  dateTo: string;
  requestNumber: string;
  page: number;
};

export function buildApprovalLeadTimeParams(filters: ApprovalLeadTimeFilters): URLSearchParams {
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

export function getApprovalLeadTime(
  filters: ApprovalLeadTimeFilters,
  signal?: AbortSignal,
): Promise<ApprovalLeadTimeResponse> {
  return httpGet<ApprovalLeadTimeResponse>(
    suppliesApiUrl(`/purchase-requests/approval-lead-time?${buildApprovalLeadTimeParams(filters).toString()}`),
    { signal },
  );
}
