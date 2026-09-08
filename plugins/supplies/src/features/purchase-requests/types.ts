export type OverallStage =
  | "awaiting_order"
  | "partially_ordered"
  | "ordered"
  | "awaiting_receipt"
  | "partially_received"
  | "completed"
  | "residual_closed";

export const OVERALL_STAGE_VALUES = [
  "awaiting_order",
  "partially_ordered",
  "ordered",
  "awaiting_receipt",
  "partially_received",
  "completed",
  "residual_closed",
] as const satisfies readonly OverallStage[];

export type PersonRef = {
  protheus_user_id?: string | null;
  code?: string | null;
  name?: string | null;
};

export type CostCenterRef = {
  code: string;
  description?: string | null;
};

export type PurchaseRequestListItem = {
  branch: string;
  request_number: string;
  request_item?: string | null;
  request_issue_date?: string | null;
  product_code?: string | null;
  product_description?: string | null;
  cost_center_code?: string | null;
  cost_center?: CostCenterRef | null;
  requester?: PersonRef | null;
  approval?: { status?: string | null };
  derived?: { overall_stage?: OverallStage | string | null };
};

export type PurchaseRequestListResponse = {
  items: PurchaseRequestListItem[];
  page: number;
  page_size: number;
  total: number;
  total_pages?: number;
};

export type PurchaseRequestDetail = {
  header: {
    branch: string;
    request_number: string;
    issue_date?: string | null;
    requester?: PersonRef | null;
    overall_stage?: OverallStage | string | null;
    approval_summary?: { status?: string | null };
    visible_items_count?: number;
    cost_centers?: CostCenterRef[];
  };
  lines: Array<{
    request_item?: string | null;
    product_code?: string | null;
    product_description?: string | null;
    requested_quantity?: number | null;
    cost_center_code?: string | null;
    derived?: { overall_stage?: string | null };
  }>;
  timeline?: Array<{ type: string; date?: string | null; label?: string | null }>;
};

export type PurchaseRequestsQuery = {
  branch: string;
  date_from: string;
  date_to: string;
  request_number: string;
  product_code: string;
  overall_stages: OverallStage[];
  page: number;
  page_size: number;
  request: string;
};

export const DEFAULT_PAGE_SIZE = 50;
