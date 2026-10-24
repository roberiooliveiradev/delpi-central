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
  /** Minha DELPI official name — present only when the Core↔Protheus link resolved. */
  display_name?: string | null;
  /** BFF proxy path for the real user photo — only when the linked profile has one. */
  photo_url?: string | null;
  /** Canonical Core user id (opaque) — present only when the mapping is proven. */
  user_id?: string | null;
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

export type PurchaseRequestStageCounts = Record<OverallStage, number>;

export type PurchaseRequestAttentionBuckets = {
  ordering: number;
  receiving: number;
  completed: number;
};

export type PurchaseRequestSummary = {
  total_requests: number;
  total_items: number;
  stage_counts: PurchaseRequestStageCounts;
  buckets: PurchaseRequestAttentionBuckets;
};

export type SupplierRef = {
  code?: string | null;
  store?: string | null;
  name?: string | null;
};

/** Approval state of a request line (C1_APROV + C1_NOMAPRO). */
export type ApprovalRef = {
  status?: string | null;
  approver_name?: string | null;
};

/**
 * Receipt linked to a purchase order line (SD1).
 * Dates are `YYYY-MM-DD` strings in `invoice_issue_date`/`entry_date`.
 */
export type PurchaseRequestReceipt = {
  branch?: string | null;
  invoice_number?: string | null;
  invoice_series?: string | null;
  invoice_item?: string | null;
  purchase_order_number?: string | null;
  purchase_order_item?: string | null;
  product_code?: string | null;
  supplier_code?: string | null;
  supplier_store?: string | null;
  quantity?: number | null;
  unit_price?: number | null;
  total_value?: number | null;
  invoice_issue_date?: string | null;
  entry_date?: string | null;
};

/**
 * Purchase order line linked to a request line (SC7 via C7_NUMSC/C7_ITEMSC).
 * `delivery_status`/`days_*`/`receipt_status` are derived by the producer —
 * delivery values are `received`/`not_applicable`/`overdue`/`on_time`
 * (producer domain vocabulary, distinct from the PC
 * `late`/`on_time`/`no_date` contract).
 */
export type PurchaseRequestLinkedOrder = {
  branch?: string | null;
  order_number?: string | null;
  order_item?: string | null;
  source_request_number?: string | null;
  source_request_item?: string | null;
  product_code?: string | null;
  product_description?: string | null;
  ordered_quantity?: number | null;
  received_quantity?: number | null;
  open_quantity?: number | null;
  issue_date?: string | null;
  expected_delivery_date?: string | null;
  supplier_code?: string | null;
  supplier_store?: string | null;
  supplier_name?: string | null;
  buyer_code?: string | null;
  order_user_protheus_user_id?: string | null;
  order_user_code?: string | null;
  order_user_name?: string | null;
  residual?: number | null;
  derived?: {
    delivery_status?: string | null;
    days_until_due?: number | null;
    days_overdue?: number | null;
    receipt_status?: string | null;
  } | null;
  receipts?: PurchaseRequestReceipt[];
};

/**
 * Derived event emitted by the producer from source dates — NOT an audit
 * trail. `expected_delivery` is a planned milestone (C7_DATPRF), not an
 * occurrence; approval/prereq changes/cancellations are not represented.
 */
export type PurchaseRequestTimelineEvent = {
  type:
    | "request_created"
    | "purchase_order_created"
    | "expected_delivery"
    | "receipt"
    | (string & {});
  date?: string | null;
  label?: string | null;
  reference?: Record<string, string | null | undefined> | null;
  metadata?: Record<string, unknown> | null;
};

export type PurchaseRequestDetailHeader = {
  branch: string;
  request_number: string;
  issue_date?: string | null;
  requester?: PersonRef | null;
  overall_stage?: OverallStage | string | null;
  approval_summary?: { status?: string | null };
  visible_items_count?: number;
  cost_centers?: CostCenterRef[];
  /**
   * Deduped purchase-order lines referenced by the visible request lines.
   * Covers only the lines authorized by the requester's CC scope.
   */
  purchase_orders?: PurchaseRequestLinkedOrder[];
  suppliers?: SupplierRef[];
  first_order_date?: string | null;
  last_order_date?: string | null;
  first_receipt_date?: string | null;
  last_receipt_date?: string | null;
  /**
   * SEMANTIC CAVEAT (P0.R1): summed across lines without grouping by `unit`
   * and over authorized lines only — NOT a reliable global-quantity KPI
   * when the request mixes units of measure. Never render as a single
   * "total quantity" indicator.
   */
  requested_quantity?: number | null;
  ordered_quantity?: number | null;
  received_quantity?: number | null;
  has_overdue_order?: boolean | null;
  max_days_overdue?: number | null;
};

export type PurchaseRequestDetailLine = {
  request_item?: string | null;
  product_code?: string | null;
  product_description?: string | null;
  requested_quantity?: number | null;
  cost_center_code?: string | null;
  /** Unit of measure for this line's quantities (C1_UM). */
  unit?: string | null;
  /** Required-by date requested for the line (C1_DATPRF). */
  request_required_date?: string | null;
  /** Quantity already converted into purchase orders (C1_QUJE). */
  ordered_quantity?: number | null;
  /** Requested minus ordered, floored at zero (C1_QUANT - C1_QUJE). */
  request_open_quantity?: number | null;
  request_issue_date?: string | null;
  requester?: PersonRef | null;
  cost_center?: CostCenterRef | null;
  /**
   * Accounting account (C1_CONTA) — per-line granularity only, preserved as
   * string with leading zeros; never aggregate across lines and never
   * confuse with cost center.
   */
  account_code?: string | null;
  approval?: ApprovalRef | null;
  /** Suggested supplier (C1_FORNECE/C1_LOJA) — a hint, not a contracted supplier. */
  suggested_supplier?: SupplierRef | null;
  /** Residual-close flag from the source (SC1 C1_RESIDUO = 'S' → 1). */
  residual?: number | null;
  purchase_orders?: PurchaseRequestLinkedOrder[];
  derived?: {
    overall_stage?: string | null;
    order_status?: string | null;
    receipt_status?: string | null;
  } | null;
};

export type PurchaseRequestDetail = {
  header: PurchaseRequestDetailHeader;
  lines: PurchaseRequestDetailLine[];
  timeline?: PurchaseRequestTimelineEvent[];
};

export type PurchaseRequestsSortDir = "asc" | "desc";

export type PurchaseRequestsQuery = {
  branches: string[];
  date_from: string;
  date_to: string;
  request_number: string;
  product_code: string;
  /** Selected requesters by `protheus_user_id` (serialized as `requester_user_id`). */
  requester_ids: string[];
  /** Selected cost-center codes (serialized as `cost_center`). */
  cost_centers: string[];
  overall_stages: OverallStage[];
  sort_by: string;
  sort_dir: PurchaseRequestsSortDir;
  page: number;
  page_size: number;
  request: string;
};

export const DEFAULT_PAGE_SIZE = 50;
