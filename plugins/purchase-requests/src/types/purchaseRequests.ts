export type ApprovalStatus = "approved" | "rejected" | "blocked" | "unknown";

export type OverallStage =
  | "awaiting_order"
  | "partially_ordered"
  | "ordered"
  | "awaiting_receipt"
  | "partially_received"
  | "completed"
  | "residual_closed";

export type DeliveryStatus = "overdue" | "on_time" | "received" | "not_applicable";

export type ReceiptStatus =
  | "not_ordered"
  | "awaiting_receipt"
  | "partially_received"
  | "received";

export type PersonRef = {
  protheus_user_id?: string | null;
  code?: string | null;
  name?: string | null;
};

export type CostCenterRef = {
  code: string;
  description?: string | null;
};

export type SupplierRef = {
  code?: string | null;
  store?: string | null;
  name?: string | null;
};

export type PurchaseOrderSummaryRef = {
  branch?: string | null;
  order_number?: string | null;
  order_item?: string | null;
  supplier_code?: string | null;
  supplier_store?: string | null;
  supplier_name?: string | null;
};

export type PurchaseRequestSummary = {
  branch: string;
  request_number: string;
  issue_date?: string | null;
  requester?: PersonRef | null;
  visible_items_count?: number;
  cost_centers?: CostCenterRef[];
  approval_summary?: { status?: ApprovalStatus | string | null };
  overall_stage?: OverallStage | string | null;
  purchase_orders?: PurchaseOrderSummaryRef[];
  suppliers?: SupplierRef[];
  first_order_date?: string | null;
  last_order_date?: string | null;
  first_receipt_date?: string | null;
  last_receipt_date?: string | null;
  requested_quantity?: number;
  ordered_quantity?: number;
  received_quantity?: number;
  has_overdue_order?: boolean;
  max_days_overdue?: number | null;
};

export type BuyerRef = {
  code?: string | null;
  name?: string | null;
} | null;

export type ReceiptLine = {
  invoice_number?: string | null;
  invoice_series?: string | null;
  invoice_item?: string | null;
  quantity?: number | null;
  invoice_issue_date?: string | null;
  entry_date?: string | null;
  purchase_order_number?: string | null;
  purchase_order_item?: string | null;
};

export type PurchaseOrderLine = {
  branch?: string | null;
  order_number?: string | null;
  order_item?: string | null;
  supplier_code?: string | null;
  supplier_store?: string | null;
  supplier_name?: string | null;
  issue_date?: string | null;
  expected_delivery_date?: string | null;
  ordered_quantity?: number | null;
  received_quantity?: number | null;
  open_quantity?: number | null;
  order_user?: string | null;
  buyer?: BuyerRef;
  receipts?: ReceiptLine[];
  derived?: {
    delivery_status?: DeliveryStatus | string | null;
    days_until_due?: number | null;
    days_overdue?: number | null;
    receipt_status?: ReceiptStatus | string | null;
  };
};

export type PurchaseRequestLine = {
  branch?: string | null;
  request_number?: string | null;
  request_item?: string | null;
  request_issue_date?: string | null;
  product_code?: string | null;
  product_description?: string | null;
  cost_center_code?: string | null;
  cost_center_description?: string | null;
  requested_quantity?: number | null;
  ordered_quantity?: number | null;
  original_need_date?: string | null;
  approval?: { status?: ApprovalStatus | string | null; approver_name?: string | null };
  requester?: PersonRef | null;
  cost_center?: CostCenterRef | null;
  suggested_supplier?: SupplierRef | null;
  purchase_orders?: PurchaseOrderLine[];
  derived?: {
    order_status?: string | null;
    receipt_status?: ReceiptStatus | string | null;
    overall_stage?: OverallStage | string | null;
  };
};

export type TimelineEvent = {
  type: string;
  date?: string | null;
  label?: string | null;
  reference?: Record<string, string | null | undefined>;
  metadata?: Record<string, unknown>;
};

export type PurchaseRequestDetail = {
  header: PurchaseRequestSummary;
  lines: PurchaseRequestLine[];
  timeline: TimelineEvent[];
};

export type Pagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type PurchaseRequestListItem = PurchaseRequestLine & {
  branch: string;
  request_number: string;
};

export type PurchaseRequestListResponse = Pagination & {
  items: PurchaseRequestListItem[];
};

export type PurchaseRequestsQuery = {
  branch: string;
  date_from: string;
  date_to: string;
  request_number: string;
  requester_user_ids: string[];
  cost_center_codes: string[];
  product_code: string;
  supplier_code: string;
  order_number: string;
  overall_stages: OverallStage[];
  page: number;
  page_size: number;
};

export type PurchaseRequestRequesterOption = {
  protheus_user_id: string;
  code?: string | null;
  name?: string | null;
};

export const DEFAULT_PAGE_SIZE = 50;

export const OVERALL_STAGE_VALUES = [
  "awaiting_order",
  "partially_ordered",
  "ordered",
  "awaiting_receipt",
  "partially_received",
  "completed",
  "residual_closed",
] as const satisfies readonly OverallStage[];

export const APPROVAL_STATUS_VALUES = ["approved", "rejected", "blocked", "unknown"] as const;

export const EMPTY_QUERY: PurchaseRequestsQuery = {
  branch: "",
  date_from: "",
  date_to: "",
  request_number: "",
  requester_user_ids: [],
  cost_center_codes: [],
  product_code: "",
  supplier_code: "",
  order_number: "",
  overall_stages: [],
  page: 1,
  page_size: DEFAULT_PAGE_SIZE,
};

export type Envelope<T> = {
  success: boolean;
  message: string;
  data: T;
};
