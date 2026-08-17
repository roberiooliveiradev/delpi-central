export const SHIPMENT_STATUS_VALUES = ["completed", "partial", "no_return"] as const;

export type ShipmentStatus = (typeof SHIPMENT_STATUS_VALUES)[number];

export const SHIPMENT_STATUS_LABELS: Record<ShipmentStatus, string> = {
  completed: "Concluído",
  partial: "Parcial",
  no_return: "Sem retorno",
};

export const BRANCH_LABELS: Record<string, string> = {
  "01": "SC (01)",
  "02": "ES (02)",
};

export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PAGE_SIZE = 100;

export type ThirdPartyMaterialsQuery = {
  branch: string;
  product: string;
  customerReference: string;
  partnerCode: string;
  partnerStore: string;
  receiptNumber: string;
  returnNumber: string;
  issuedFrom: string;
  issuedTo: string;
  status: ShipmentStatus | "";
  onlyWithBalance: boolean;
  includeTestProducts: boolean;
};

export const EMPTY_QUERY: ThirdPartyMaterialsQuery = {
  branch: "",
  product: "",
  customerReference: "",
  partnerCode: "",
  partnerStore: "",
  receiptNumber: "",
  returnNumber: "",
  issuedFrom: "",
  issuedTo: "",
  status: "",
  onlyWithBalance: false,
  includeTestProducts: false,
};

export type ProductInfo = {
  code: string;
  customer_reference: string | null;
  description: string | null;
  unit: string | null;
  type: string | null;
  group: string | null;
  blocked: boolean;
};

export type PartnerInfo = {
  type: string | null;
  code: string | null;
  store: string | null;
  name: string | null;
  short_name: string | null;
  blocked: boolean;
};

export type ReceiptInvoice = {
  number: string | null;
  series: string | null;
  issued_on: string | null;
  posted_on: string | null;
  tes: string | null;
};

export type ShipmentReturn = {
  return_recno: number;
  number: string | null;
  series: string | null;
  issued_on: string | null;
  posted_on: string | null;
  tes: string | null;
  quantity: number;
  accumulated_returned_quantity: number;
  balance_after_return: number;
  partner_type: string | null;
  partner_code: string | null;
  partner_store: string | null;
};

export type Shipment = {
  shipment_recno: number;
  branch: string;
  shipment_id: string;
  product: ProductInfo;
  partner: PartnerInfo;
  receipt_invoice: ReceiptInvoice;
  received_quantity: number;
  returned_quantity: number;
  pending_balance: number;
  status: ShipmentStatus | string;
  has_balance: boolean;
  attended_indicator: string | null;
  summed_return_quantity: number;
  control_difference: number;
  returns: ShipmentReturn[];
};

export type ShipmentsPage = {
  items: Shipment[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  is_complete?: boolean;
};

export type SummaryData = {
  total_shipments: number;
  open_shipments: number;
  partial_shipments: number;
  no_return_shipments: number;
  pending_balance: number;
};

export function hasUsefulScope(query: ThirdPartyMaterialsQuery): boolean {
  if (!query.branch.trim()) return false;
  return Boolean(
    query.product.trim() ||
      query.customerReference.trim() ||
      query.receiptNumber.trim() ||
      query.returnNumber.trim() ||
      query.issuedFrom.trim() ||
      query.issuedTo.trim() ||
      query.onlyWithBalance,
  );
}
