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
  | "post_manual";

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
