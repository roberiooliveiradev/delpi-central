export type InventoryStockItem = {
  product_code: string | null;
  description: string | null;
  unit_of_measure: string | null;
  branch: string | null;
  warehouse: string | null;
  warehouse_label: string | null;
  quantity: number | null;
  unit_cost: number | null;
  stock_value: number | null;
};

export type InventoryByWarehouse = {
  branch: string | null;
  warehouse: string | null;
  warehouse_label: string | null;
  product_count?: number | null;
  total_quantity?: number | null;
  total_stock_value?: number | null;
  total_stock_value_vatu1?: number | null;
};

export type InventoryStockSummary = {
  product_count: number;
  warehouse_count: number;
  total_stock_value: number;
  total_quantity?: number | null;
  total_stock_value_vatu1?: number | null;
  valuation?: string | null;
  branch?: string | null;
  warehouse?: string | null;
};

export type InventorySummaryResponse = {
  summary: InventoryStockSummary;
  by_warehouse: InventoryByWarehouse[];
  applied_filters?: Record<string, unknown>;
};

export type InventoryItemsResponse = {
  items: InventoryStockItem[];
  page: number;
  page_size: number;
  total: number;
  total_pages?: number;
  sort?: string;
  pagination?: Record<string, unknown>;
  applied_filters?: Record<string, unknown>;
};

export const EMPTY_INVENTORY_SUMMARY: InventoryStockSummary = {
  product_count: 0,
  warehouse_count: 0,
  total_stock_value: 0,
};

/** BFF allow-list — do not invent sort tokens. */
export const INVENTORY_ALLOWED_SORT = [
  "stock_value_desc",
  "stock_value_asc",
  "quantity_desc",
  "quantity_asc",
  "product_code_asc",
  "product_code_desc",
] as const;

export type InventorySort = (typeof INVENTORY_ALLOWED_SORT)[number];

export const DEFAULT_INVENTORY_SORT: InventorySort = "stock_value_desc";

export type InventoryQuery = {
  branches: string[];
  /** Empty = all warehouses (omit warehouse query). Never invent a code for B2_LOCAL=''. */
  warehouse: string;
  sort: InventorySort;
  page: number;
  page_size: number;
};

export const DEFAULT_PAGE_SIZE = 50;
export const INVENTORY_PAGE_SIZE_OPTIONS = [50, 100, 200] as const;

export type InventorySortableColumnKey =
  | "product_code"
  | "quantity"
  | "stock_value";

export const INVENTORY_SORTABLE_COLUMNS: Record<
  InventorySortableColumnKey,
  "product_code" | "quantity" | "stock_value"
> = {
  product_code: "product_code",
  quantity: "quantity",
  stock_value: "stock_value",
};
