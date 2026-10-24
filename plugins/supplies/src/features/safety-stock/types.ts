/**
 * E11 — Estoque de Segurança (safety stock).
 * Contrato BFF: supplies-api `GET /safety-stock/*` (composição upstream do produtor).
 * O Portal não recalcula classificação, déficit nem saldos — passthrough.
 */

export type SafetyStockStatus =
  | "without_safety_stock"
  | "below_safety_stock"
  | "at_safety_stock"
  | "above_safety_stock";

export const SAFETY_STOCK_STATUSES: readonly SafetyStockStatus[] = [
  "without_safety_stock",
  "below_safety_stock",
  "at_safety_stock",
  "above_safety_stock",
];

/** Escopo de filial é filtro: uma consulta `all` consolidada, nunca fan-out. */
export type SafetyStockBranchScope = "all" | "01" | "02";

export const SAFETY_STOCK_ALL_SCOPE: SafetyStockBranchScope = "all";
export const SAFETY_STOCK_BRANCH_SCOPES: readonly SafetyStockBranchScope[] = [
  "all",
  "01",
  "02",
];

/** BFF allow-list de sortBy (9 campos) — não inventar tokens. */
export const SAFETY_STOCK_SORT_FIELDS = [
  "product_code",
  "product_description",
  "product_group",
  "unit",
  "safety_stock",
  "primary_stock",
  "work_in_process_stock",
  "deficit_quantity",
  "status",
] as const;

export type SafetyStockSortField = (typeof SAFETY_STOCK_SORT_FIELDS)[number];

export type SafetyStockSortDirection = "asc" | "desc";

export const DEFAULT_SAFETY_STOCK_SORT_FIELD: SafetyStockSortField =
  "product_code";
export const DEFAULT_SAFETY_STOCK_SORT_DIRECTION: SafetyStockSortDirection =
  "asc";

export const DEFAULT_PAGE_SIZE = 50;
export const MAX_PAGE_SIZE = 200;
export const SAFETY_STOCK_PAGE_SIZE_OPTIONS = [50, 100, 200] as const;

export type SafetyStockQuery = {
  branch: SafetyStockBranchScope;
  status: SafetyStockStatus | "";
  productGroup: string;
  unit: string;
  search: string;
  includeBlocked: boolean;
  includeWithoutSafetyStock: boolean;
  sortBy: SafetyStockSortField;
  sortDirection: SafetyStockSortDirection;
  page: number;
  page_size: number;
};

export type SafetyStockItem = {
  product_code: string | null;
  product_description: string | null;
  product_type: string | null;
  product_group: string | null;
  unit: string | null;
  branch: string | null;
  blocked?: boolean | null;
  safety_stock: number | null;
  primary_stock: number | null;
  work_in_process_stock: number | null;
  deficit_quantity: number | null;
  status: string | null;
};

export type SafetyStockDeficitByUnit = {
  unit: string;
  material_count: number;
  deficit_quantity: number;
};

export type SafetyStockSummary = {
  total_materials: number;
  with_safety_stock: number;
  without_safety_stock: number;
  below_safety_stock: number;
  at_safety_stock: number;
  above_safety_stock: number;
  with_primary_stock: number;
  without_primary_stock: number;
  with_work_in_process_stock: number;
  deficit_by_unit: SafetyStockDeficitByUnit[];
};

export type SafetyStockFiltersResponse = {
  branch: string;
  /** Catálogo operacional do Portal (OPERATIONAL_UNITS) — fonte das opções. */
  branch_catalog: string[];
  all_scope: string;
  product_groups: string[];
  units: string[];
  statuses: string[];
  warehouses?: unknown;
  primary_warehouse?: unknown;
  work_in_process_warehouses?: unknown;
  work_in_process_note?: string;
};

export type SafetyStockItemsResponse = {
  items: SafetyStockItem[];
  page: number;
  page_size: number;
  total: number;
  total_pages?: number;
  sort_by?: string;
  sort_direction?: string;
};
