export type PartyType = "customer" | "supplier";
export type InvoiceType =
  | "sale"
  | "return"
  | "sample"
  | "repair_shipment"
  | "other";
export type FreightMode = "cif" | "fob";
export type IssuanceStatus =
  | "pending"
  | "in_progress"
  | "issued"
  | "returned"
  | "cancelled";

export type AllowedAction =
  | "view"
  | "edit"
  | "resubmit"
  | "start"
  | "return"
  | "issue"
  | "cancel";

export type Party = {
  party_type: PartyType;
  party_code: string;
  party_store: string;
  party_name: string;
  tax_id: string | null;
  blocked: boolean;
};

export type ProductHit = {
  code: string;
  description: string;
  unit: string | null;
  blocked: boolean;
};

export type Carrier = {
  carrier_code: string;
  carrier_name: string;
  legal_name: string | null;
  tax_id: string | null;
  address?: string | null;
  phone?: string | null;
  blocked: boolean;
};

export type WarehouseBalance = {
  product_code: string;
  branch_code: string;
  warehouse: string;
  quantity: number;
};

export type IssuanceItem = {
  id?: string;
  line_number?: number;
  product_code: string;
  product_description: string;
  quantity: number;
  unit_price: number;
  stock_write_off: boolean;
  sales_order?: string | null;
  sales_order_item?: string | null;
  customer_order_number?: string | null;
};

export type OpenSalesOrderLine = {
  sales_order: string;
  sales_order_item: string;
  customer_order_number: string | null;
  product_code: string;
  product_description: string;
  quantity_ordered: number;
  quantity_delivered: number;
  quantity_open: number;
  unit_price: number;
  open_amount: number;
  stock_on_hand: number;
};

export type OpenSalesOrderGroup = {
  sales_order: string;
  customer_order_number: string | null;
  branch_code: string;
  lines: OpenSalesOrderLine[];
  lines_count: number;
  open_quantity: number;
  open_amount: number;
};

export type ChecklistFlags = {
  recipient: boolean;
  item_codes: boolean;
  quantity_price: boolean;
  stock_write_off: boolean;
  invoice_type: boolean;
  freight_mode: boolean;
  weight_volumes: boolean;
};

export type IssuanceAttachment = {
  id: string;
  original_name: string;
  mime_type: string;
  size_bytes: number;
  created_at: string;
};

export type HistoryEvent = {
  id: string;
  event_type: string;
  actor_name: string | null;
  from_status: string | null;
  to_status: string | null;
  justification: string | null;
  created_at: string;
};

export type IssuanceRequest = {
  id: string;
  branch_code: string;
  party_type: PartyType;
  party_code: string;
  party_store: string;
  party_name: string;
  tax_id: string | null;
  invoice_type: InvoiceType;
  invoice_type_other: string | null;
  freight_mode: FreightMode;
  carrier_code: string | null;
  carrier_name: string | null;
  carrier_legal_name?: string | null;
  carrier_tax_id?: string | null;
  carrier_address?: string | null;
  carrier_phone?: string | null;
  weight_kg: number;
  volume_count: number;
  purchase_order_number: string | null;
  observation: string | null;
  status: IssuanceStatus;
  return_reason: string | null;
  checklist: ChecklistFlags;
  created_by_user_id: string;
  created_by_name: string;
  assignee_user_id: string | null;
  assignee_name: string | null;
  cancelled_at: string | null;
  cancelled_by_name: string | null;
  cancel_justification: string | null;
  issued_at: string | null;
  created_at: string;
  updated_at: string;
  items: IssuanceItem[];
  attachments: IssuanceAttachment[];
  items_count?: number;
  total_amount?: number;
};

export type RequestDetail = {
  request: IssuanceRequest;
  history: HistoryEvent[];
  allowed_actions: AllowedAction[];
};

export type ListFilters = {
  page: number;
  page_size: number;
  status?: string;
  branch: string;
  invoice_type?: string;
  q?: string;
};
