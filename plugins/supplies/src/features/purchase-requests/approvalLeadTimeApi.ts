import { httpGet, suppliesApiUrl } from "../../api/httpClient";

export type ApprovalRequestProduct = {
  product_code: string;
  product_description: string | null;
  line_count: number;
};

export type ApprovalLeadTimeEvent = {
  level: string;
  approved_at: string;
  action_user_code: string;
  approver_code: string;
  approver_name: string | null;
  approver_user_code: string | null;
};

export type ApprovalPendingApprover = {
  level: string;
  approver_code: string;
  approver_name: string | null;
  approver_user_code: string | null;
  pending_since: string | null;
  waiting_days: number | null;
};

export type ApprovalPendingRequest = {
  branch: string;
  request_number: string;
  issue_date: string;
  requester_name: string | null;
  sc1_approved: boolean;
  products: ApprovalRequestProduct[];
  pending_approvers: ApprovalPendingApprover[];
};

export type ApprovalApproverStats = {
  approver_code: string;
  approver_name: string;
  approver_user_code: string | null;
  approvals: number;
  avg_days: number | null;
  max_days: number | null;
  same_day: number;
  pending_count: number;
};

export type ApprovalLeadTimeRecord = {
  branch: string;
  request_number: string;
  issue_date: string;
  requester_name: string | null;
  requester_user_id: string | null;
  item_count: number;
  products: ApprovalRequestProduct[];
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
    pending_requests: number;
  };
  approver_stats: ApprovalApproverStats[];
  pending_items: ApprovalPendingRequest[];
  pending_total: number;
  pending_truncated: boolean;
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
