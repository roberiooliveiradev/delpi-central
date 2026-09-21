export type DeliveryPunctualityStatus = "late" | "on_time";

export type DeliveryLateListItem = {
  branch: string;
  order_number: string;
  order_item?: string | null;
  product_code?: string | null;
  product_description?: string | null;
  supplier_code?: string | null;
  supplier_store?: string | null;
  supplier_name?: string | null;
  supplier_short_name?: string | null;
  quantity?: number | null;
  expected_delivery_date?: string | null;
  receipt_entry_date?: string | null;
  days_diff?: number | null;
  status?: DeliveryPunctualityStatus | string | null;
};

export type DeliveryLateSummary = {
  total_lines: number;
  on_time_lines: number;
  late_lines: number;
  purchase_order_otd_pct?: number | null;
  late_percentage?: number | null;
};

export type DeliveryLateListResponse = {
  items: DeliveryLateListItem[];
  page: number;
  page_size: number;
  total: number;
  total_pages?: number;
  summary?: DeliveryLateSummary;
  applied_filters?: Record<string, unknown>;
};

export const EMPTY_DELIVERY_LATE_SUMMARY: DeliveryLateSummary = {
  total_lines: 0,
  on_time_lines: 0,
  late_lines: 0,
};

export type DeliveriesSortDir = "asc" | "desc";

export type DeliveriesQuery = {
  branches: string[];
  status: DeliveryPunctualityStatus;
  start_date: string;
  end_date: string;
  sort_by: string;
  sort_dir: DeliveriesSortDir;
  page: number;
  page_size: number;
};

export const DEFAULT_PAGE_SIZE = 20;
export const DELIVERIES_PAGE_SIZE_OPTIONS = [20, 50, 100] as const;

export const DELIVERY_STATUS_OPTIONS: {
  value: DeliveryPunctualityStatus;
  label: string;
}[] = [
  { value: "late", label: "Em atraso" },
  { value: "on_time", label: "No prazo" },
];
