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

/* ------------------------------------------------------------------ */
/* E11.S3 — detalhe do item (contrato produtor, passthrough pelo BFF)   */
/* ------------------------------------------------------------------ */

export type SafetyStockCollectionBlock<T> = {
  items: T[];
  total: number;
  summary?: Record<string, unknown>;
};

export type SafetyStockDetailProduct = {
  product_code: string | null;
  product_description: string | null;
  product_type: string | null;
  unit: string | null;
  secondary_unit: string | null;
  conversion_factor: number | null;
  conversion_type: string | null;
  product_group: string | null;
  branch: string | null;
  blocked: boolean | null;
  status: string | null;
};

export type SafetyStockDetailStock = {
  safety_stock: number | null;
  available_stock: number | null;
  primary_stock: number | null;
  warehouse_50_stock: number | null;
  warehouse_98_stock: number | null;
  warehouse_99_stock: number | null;
  work_in_process_stock: number | null;
  work_in_process_committed: number | null;
  work_in_process_available: number | null;
  deficit_quantity: number | null;
  last_inventory_date: string | null;
};

export type SafetyStockPurchaseCoverage = {
  status: string | null;
  deficit_quantity: number | null;
  eligible_open_quantity: number | null;
  remaining_to_buy: number | null;
  open_order_count: number | null;
  eligible_order_count: number | null;
  next_expected_delivery_date: string | null;
  incompatible_unit_order_count: number | null;
  warnings: string[];
};

export type SafetyStockOpenPurchaseOrder = {
  branch: string | null;
  order_number: string | null;
  order_item: string | null;
  supplier_part_number: string | null;
  warehouse: string | null;
  unit: string | null;
  ordered_quantity: number | null;
  delivered_quantity: number | null;
  open_quantity: number | null;
  open_quantity_primary_unit: number | null;
  issue_date: string | null;
  expected_delivery_date: string | null;
  supplier_code: string | null;
  supplier_store: string | null;
  supplier_name: string | null;
  unit_price: number | null;
  open_value: number | null;
  unit_compatible?: boolean | null;
  warehouse_eligible?: boolean | null;
  coverage_eligible?: boolean | null;
};

export type SafetyStockOpenPurchaseRequest = {
  branch: string | null;
  request_number: string | null;
  request_item: string | null;
  warehouse: string | null;
  unit: string | null;
  requested_quantity: number | null;
  ordered_quantity: number | null;
  open_quantity: number | null;
  open_quantity_primary_unit: number | null;
  issue_date: string | null;
  required_date: string | null;
  supplier_code: string | null;
  supplier_store: string | null;
  supplier_name: string | null;
  purchase_order_number: string | null;
  unit_price: number | null;
  total_value: number | null;
  unit_compatible?: boolean | null;
};

export type SafetyStockOpenCommitment = {
  branch: string | null;
  warehouse: string | null;
  production_order: string | null;
  commitment_date: string | null;
  unit: string | null;
  original_quantity: number | null;
  open_quantity: number | null;
  open_quantity_primary_unit: number | null;
  consumed_quantity: number | null;
  finished_production_order: string | null;
  finished_product_code: string | null;
  finished_order_observation: string | null;
  unit_compatible?: boolean | null;
  projection_eligible?: boolean | null;
};

export type SafetyStockProjectionEvent = {
  sequence: number;
  event_date: string | null;
  date_status: string | null;
  date_semantics: string | null;
  origin: string | null;
  origin_label: string | null;
  reference: string | null;
  finished_production_order: string | null;
  finished_product_code: string | null;
  warehouse: string | null;
  movement: number | null;
  inflow: number | null;
  outflow: number | null;
  running_balance: number | null;
  unit_compatible?: boolean | null;
  projection_eligible?: boolean | null;
};

export type SafetyStockProjectionSummary = {
  as_of_date: string | null;
  initial_balance: number | null;
  safety_stock: number | null;
  eligible_purchase_quantity: number | null;
  eligible_commitment_quantity: number | null;
  final_projected_balance: number | null;
  final_balance_after_safety: number | null;
  minimum_projected_balance: number | null;
  first_shortage_date: string | null;
  projected_remaining_to_buy: number | null;
  status: string | null;
  warnings: string[];
};

export type SafetyStockStockProjection = {
  items: SafetyStockProjectionEvent[];
  total: number;
  summary?: SafetyStockProjectionSummary;
};

export type SafetyStockMonthlyConsumptionPoint = {
  year_month: string | null;
  year_month_label: string | null;
  consumption_quantity: number | null;
  movement_count: number | null;
};

export type SafetyStockMonthlyConsumption = {
  items: SafetyStockMonthlyConsumptionPoint[];
  total: number;
  period_consumption: number | null;
  period_start: string | null;
  period_end: string | null;
};

export type SafetyStockAnnualComparisonItem = {
  month: number;
  month_label: string;
  values_by_year: Record<string, number | null>;
};

export type SafetyStockAnnualComparison = {
  years: string[];
  items: SafetyStockAnnualComparisonItem[];
  total: number;
  period_start: string | null;
  period_end: string | null;
};

export type SafetyStockItemDetail = {
  product: SafetyStockDetailProduct;
  stock: SafetyStockDetailStock;
  purchase_coverage?: SafetyStockPurchaseCoverage;
  open_purchase_orders?: SafetyStockCollectionBlock<SafetyStockOpenPurchaseOrder>;
  open_purchase_requests?: SafetyStockCollectionBlock<SafetyStockOpenPurchaseRequest>;
  open_commitments?: SafetyStockCollectionBlock<SafetyStockOpenCommitment>;
  stock_projection?: SafetyStockStockProjection;
  monthly_consumption?: SafetyStockMonthlyConsumption;
  annual_comparison?: SafetyStockAnnualComparison;
};

export type SafetyStockLinkedSupplier = {
  product_code: string | null;
  supplier_code: string | null;
  supplier_store: string | null;
  supplier_part_number: string | null;
  trade_name: string | null;
  legal_name: string | null;
  document: string | null;
  has_last_purchase: boolean;
  last_purchase_date: string | null;
  last_unit_price: number | null;
  last_quantity: number | null;
  last_total_value: number | null;
  last_invoice_number: string | null;
  last_invoice_series: string | null;
};

export type SafetyStockSuppliersResponse = SafetyStockCollectionBlock<SafetyStockLinkedSupplier>;

/** Alvo de abertura do detalhe — identidade composta produto + filial. */
export type SafetyStockDetailTarget = {
  productCode: string;
  branch: string;
};
