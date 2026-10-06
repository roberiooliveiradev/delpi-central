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

export type LinkedPurchaseOrderLine = {
  order_item: string;
  product_code?: string | null;
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
  /** Vazio/ausente = grupo inteiro (legado V005). */
  lines?: LinkedPurchaseOrderLine[];
};

export type FiscalModel = "nfe" | "nfse" | "cte";

export type LinkedInvoice = {
  document_number: string;
  series: string;
};

export type InvoicePostingRequest = {
  id: string;
  branch_code: string;
  document_number: string;
  document_match_key: string;
  series: string;
  fiscal_model: FiscalModel | null;
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
  linked_purchase_orders: LinkedPurchaseOrderSnapshot[];
  linked_invoices?: LinkedInvoice[];
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
  danfe?: InvoicePostingDanfe | null;
  fiscal_attachments?: FiscalAttachment[];
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
  /** Código do produto no fornecedor (SA5.A5_CODPRF). */
  supplier_part_number?: string;
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
  open_merchandise_value: number;
  open_ipi_value: number;
  open_freight_value?: number;
  open_discount_value?: number;
  open_value: number;
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
  linked: LinkedPurchaseOrderSnapshot[];
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
  fiscal_model: FiscalModel;
  supplier_code: string;
  supplier_store: string;
  issue_date: string;
  amount: number | string;
  received_at: string;
  observation?: string | null;
  source?: "manual" | "received_nfe" | "questor";
  document_id?: string;
  access_key?: string;
  provider_entity_id?: string;
  source_branch?: string;
  source_document_type?: "nfe" | "nfse" | "cte";
  provider_document_number?: string;
  provider_file_id?: string;
  linked_invoices?: Array<{ document: string; series: string }>;
};

export type ReceivedDocumentType = "nfe" | "nfse" | "cte";

export type ReceivedInvoiceItem = {
  documentType?: ReceivedDocumentType;
  documentId: string;
  providerEntityId?: string | null;
  providerFileId?: string | null;
  providerDocumentNumber?: string | null;
  documentNumber?: string | null;
  accessKey: string;
  invoiceNumber: string;
  series: string;
  issuerName: string;
  issuerCnpj: string | null;
  receiverName?: string | null;
  receiverCnpj?: string | null;
  emissionAt: string | null;
  amount: string;
  amountFormatted: string;
  cityHall?: string | null;
  danfeAvailable: boolean;
  printableAvailable?: boolean;
  xmlOriginalAvailable?: boolean;
  xmlStandardAvailable?: boolean;
  branchCode: string;
};

export type NfseServiceLine = {
  serviceCode?: string | null;
  description?: string | null;
  issRate?: string | null;
  serviceAmount?: string | null;
  nbs?: string | null;
  ibsCbs?: Record<string, string> | null;
};

export type NfseDetail = {
  documentId?: string;
  branchCode?: string;
  documentType?: "nfse";
  cityHall?: string | null;
  number?: string | null;
  series?: string | null;
  providerDocumentKey?: string | null;
  emissionDate?: string | null;
  competence?: string | null;
  verificationCode?: string | null;
  rpsNumber?: string | null;
  serviceCode?: string | null;
  providerName?: string | null;
  providerCnpj?: string | null;
  takerName?: string | null;
  takerCnpj?: string | null;
  pis?: string | null;
  cofins?: string | null;
  csll?: string | null;
  iss?: string | null;
  ir?: string | null;
  inss?: string | null;
  netAmount?: string | null;
  services?: NfseServiceLine[];
};

export type CteLinkedInvoice = {
  accessKey: string;
  documentNumber: string;
  series: string;
};

export type CteParty = {
  name?: string | null;
  cnpj?: string | null;
};

export type CtePlace = {
  city?: string | null;
  state?: string | null;
};

export type CteDetail = {
  documentType?: "cte";
  documentId?: string;
  providerFileId?: string | null;
  branchCode?: string;
  accessKey?: string | null;
  number?: string | null;
  series?: string | null;
  model?: string | null;
  emissionAt?: string | null;
  issuer?: CteParty | null;
  sender?: CteParty | null;
  recipient?: CteParty | null;
  origin?: CtePlace | null;
  destination?: CtePlace | null;
  serviceValue?: string | null;
  cargoValue?: string | null;
  linkedInvoices?: CteLinkedInvoice[];
};

export type NfeMappingStatus = "mapped" | "unmapped" | "ambiguous";

export type NfeProductMappingState = "supplier_required" | "issuer_mismatch" | "ready";

export type NfeMappedItem = {
  itemNumber?: string | null;
  supplierProductCode?: string | null;
  supplierProductDescription?: string | null;
  internalProductCode?: string | null;
  internalProductDescription?: string | null;
  quantity?: string | null;
  unit?: string | null;
  mappingStatus?: NfeMappingStatus | null;
};

export type NfeItemDetail = {
  documentType?: "nfe";
  documentId?: string;
  providerEntityId?: string;
  branchCode?: string;
  accessKey?: string;
  number?: string | null;
  series?: string | null;
  emissionAt?: string | null;
  issuer?: { name?: string | null; cnpj?: string | null } | null;
  productMapping?: { state?: NfeProductMappingState | null } | null;
  items?: NfeMappedItem[];
  summary?: {
    items: number;
    mapped: number;
    unmapped: number;
    ambiguous: number;
  };
};

export type FiscalAttachment = {
  document_type: string;
  attachment_type: "xml_original" | "xml_standard" | "danfe" | "dacte";
  provider_document_id: string;
  provider_document_number: string;
  provider_document_key?: string | null;
  branch_code: string;
  file_name: string;
  content_type: string;
  size_bytes: number;
};

export type ReceivedInvoiceSearch = {
  items: ReceivedInvoiceItem[];
  pagination: {
    page: number;
    pageSize: number;
    totalItems: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
};

export type InvoicePostingDanfe = {
  available: boolean;
  document_id: string;
  access_key: string;
  provider_entity_id?: string | null;
  file_name: string;
  size_bytes: number;
};

export type UpdateRequestPayload = {
  branch?: string;
  document?: string;
  series?: string | null;
  fiscal_model?: FiscalModel | null;
  supplier_code?: string;
  supplier_store?: string;
  issue_date?: string;
  amount?: number | string;
  received_at?: string;
  observation?: string | null;
};
