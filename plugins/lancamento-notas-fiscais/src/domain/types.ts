/** Tipos alinhados ao contrato real da api-delpi (lançamento-notas-fiscais). */

export type InvoicePostingStatus =
  | "pending"
  | "in_progress"
  | "blocked"
  | "posted"
  | "cancelled";

export type BlockReason =
  | "purchase_order"
  | "supplier_registration"
  | "information_correction"
  | "other";

export type AllowedAction =
  | "view"
  | "edit"
  | "start"
  | "block"
  | "resume"
  | "cancel"
  | "comment"
  | "post_manual"
  | "link_purchase_order";

export type Supplier = {
  supplier_code: string;
  supplier_store: string;
  supplier_name: string;
  supplier_short_name: string | null;
  tax_id: string | null;
  state: string | null;
  blocked: boolean;
};

export type InvoicePostingRequest = {
  id: string;
  branch_code: string;
  document_number: string;
  document_match_key: string;
  series: string;
  supplier_code: string;
  supplier_store: string;
  supplier_name: string;
  supplier_short_name: string | null;
  issue_date: string;
  amount: number;
  received_at: string;
  observation: string | null;
  status: InvoicePostingStatus;
  block_reason: BlockReason | string | null;
  block_description: string | null;
  created_by_user_id: string;
  created_by_name: string;
  assignee_user_id: string | null;
  assignee_name: string | null;
  cancelled_at: string | null;
  cancelled_by_user_id: string | null;
  cancelled_by_name: string | null;
  cancel_justification: string | null;
  completion_source: string | null;
  sf1_recno: number | null;
  erp_entry_date: string | null;
  reconciled_at: string | null;
  divergence_alert: boolean;
  divergence_detected_at: string | null;
  divergence_detail: string | null;
  linked_po_number: string | null;
  linked_po_delivery_date: string | null;
  linked_po_issue_date: string | null;
  linked_po_open_value: number | null;
  linked_po_product_count: number | null;
  linked_po_linked_at: string | null;
  linked_po_linked_by_user_id: string | null;
  linked_po_linked_by_name: string | null;
  created_at: string;
  updated_at: string;
};

export type InvoicePostingHistory = {
  id: string;
  request_id: string;
  event_type: string;
  actor_origin: string;
  actor_user_id: string | null;
  actor_name: string | null;
  from_status: string | null;
  to_status: string | null;
  changes: Record<string, unknown>;
  justification: string | null;
  created_at: string;
};

export type InvoicePostingComment = {
  id: string;
  request_id: string;
  author_user_id: string;
  author_name: string;
  body: string;
  created_at: string;
};

export type InvoicePostingDetail = {
  request: InvoicePostingRequest;
  history: InvoicePostingHistory[];
  comments: InvoicePostingComment[];
  allowed_actions: AllowedAction[];
};

export type InvoicePostingListResponse = {
  items: InvoicePostingRequest[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type OpenPurchaseOrderItem = {
  branch: string;
  order_number: string;
  order_item: string;
  product_code: string;
  product_description: string;
  warehouse: string;
  unit: string;
  ordered_quantity: number;
  delivered_quantity: number;
  open_quantity: number;
  pre_invoice_quantity: number;
  issue_date: string | null;
  expected_delivery_date: string | null;
  supplier_code: string;
  supplier_store: string;
  supplier_name: string;
  unit_price: number;
  open_value: number;
};

export type LinkedPurchaseOrderSnapshot = {
  order_number: string;
  delivery_date: string | null;
  issue_date: string | null;
  open_value: number | null;
  product_count: number | null;
  linked_at: string | null;
  linked_by_user_id: string | null;
  linked_by_name: string | null;
};

export type OpenPurchaseOrderGroup = {
  order_number: string;
  delivery_date: string | null;
  issue_date: string | null;
  product_count: number;
  open_value: number;
  item_count: number;
  items: OpenPurchaseOrderItem[];
};

export type OpenPurchaseOrdersResponse = {
  request_id: string;
  branch_code: string;
  supplier_code: string;
  supplier_store: string;
  supplier_name: string | null;
  order_count: number;
  group_count: number;
  item_count: number;
  groups: OpenPurchaseOrderGroup[];
  linked: LinkedPurchaseOrderSnapshot | null;
  can_link: boolean;
};

export type ListFilters = {
  branch?: string;
  status?: string;
  supplier?: string;
  document?: string;
  issued_from?: string;
  issued_to?: string;
  received_from?: string;
  received_to?: string;
  page?: number;
  page_size?: number;
};

export type CreateRequestPayload = {
  branch: string;
  document: string;
  series?: string | null;
  supplier_code: string;
  supplier_store: string;
  issue_date: string;
  amount: number | string;
  received_at: string;
  observation?: string | null;
};

export type UpdateRequestPayload = {
  branch?: string;
  document?: string;
  series?: string | null;
  supplier_code?: string;
  supplier_store?: string;
  issue_date?: string;
  amount?: number | string;
  received_at?: string;
  observation?: string | null;
};
