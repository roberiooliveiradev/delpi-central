export type DeliveryStatus = "late" | "on_time" | "no_date";

export type PurchaseOrderListItem = {
  branch: string;
  order_number: string;
  order_item?: string | null;
  product_code?: string | null;
  product_description?: string | null;
  ordered_quantity?: number | null;
  delivered_quantity?: number | null;
  open_quantity?: number | null;
  issue_date?: string | null;
  expected_delivery_date?: string | null;
  supplier_code?: string | null;
  supplier_store?: string | null;
  supplier_name?: string | null;
  unit_price?: number | null;
  open_value?: number | null;
  delivery_status?: DeliveryStatus | string | null;
};

export type PurchaseOrderListResponse = {
  items: PurchaseOrderListItem[];
  page: number;
  page_size: number;
  total: number;
  total_pages?: number;
};

export type PurchaseOrdersQuery = {
  branch: string;
  order_number: string;
  product_code: string;
  supplier_code: string;
  expected_delivery_from: string;
  expected_delivery_to: string;
  late_only: boolean;
  page: number;
  page_size: number;
  order: string;
};

export const DEFAULT_PAGE_SIZE = 50;
