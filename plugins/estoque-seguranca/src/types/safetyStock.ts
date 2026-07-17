export type SafetyStockStatus =
  | "without_safety_stock"
  | "below_safety_stock"
  | "at_safety_stock"
  | "above_safety_stock";

export type SafetyStockSortField =
  | "product_code"
  | "product_description"
  | "product_group"
  | "unit"
  | "safety_stock"
  | "primary_stock"
  | "work_in_process_stock"
  | "deficit_quantity"
  | "status";

export type SortDirection = "asc" | "desc";

export type SafetyStockFiltersData = {
  branch: string;
  product_groups: string[];
  units: string[];
  statuses: SafetyStockStatus[];
  warehouses: string[];
  primary_warehouse: string;
  work_in_process_warehouses: string[];
  work_in_process_note: string;
  authorized_branches: string[];
};

export type DeficitByUnitRow = {
  unit: string;
  material_count: number;
  deficit_quantity: number;
};

export type SafetyStockSummaryData = {
  total_materials: number;
  with_safety_stock: number;
  without_safety_stock: number;
  below_safety_stock: number;
  at_safety_stock: number;
  above_safety_stock: number;
  with_primary_stock: number;
  without_primary_stock: number;
  with_work_in_process_stock: number;
  deficit_by_unit: DeficitByUnitRow[];
};

export type SafetyStockItem = {
  product_code: string;
  product_description: string;
  product_type: string;
  unit: string;
  product_group: string;
  branch: string;
  blocked: boolean;
  safety_stock: number;
  primary_stock: number;
  work_in_process_stock: number;
  warehouse_50_stock: number;
  warehouse_98_stock: number;
  warehouse_99_stock: number;
  work_in_process_committed: number;
  work_in_process_available: number;
  deficit_quantity: number;
  status: SafetyStockStatus;
};

export type SafetyStockItemsData = {
  items: SafetyStockItem[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  sort_by: SafetyStockSortField;
  sort_direction: SortDirection;
};

export type PurchaseCoverageStatus = "sufficient" | "partial" | "none";

export type StockProjectionStatus =
  | "sufficient"
  | "temporary_shortage"
  | "projected_deficit";

export type StockProjectionDateStatus =
  | "today"
  | "scheduled"
  | "overdue"
  | "unscheduled";

export type StockProjectionOrigin =
  | "initial_balance"
  | "commitment"
  | "purchase_order";

export type SafetyStockOpenPurchaseOrder = {
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
  open_quantity_primary_unit: number | null;
  pre_invoice_quantity: number;
  issue_date: string | null;
  expected_delivery_date: string | null;
  supplier_code: string;
  supplier_store: string;
  supplier_name: string;
  unit_price: number;
  open_value: number;
  unit_compatible: boolean;
  unit_conversion_reason: string | null;
  warehouse_eligible: boolean;
  coverage_eligible: boolean;
};

export type SafetyStockOpenCommitment = {
  branch: string;
  product_code: string;
  product_description: string;
  warehouse: string;
  production_order: string;
  origin_production_order: string;
  commitment_date: string | null;
  unit: string;
  original_quantity: number;
  open_quantity: number;
  open_quantity_primary_unit: number | null;
  consumed_quantity: number;
  lot: string;
  commitment_sequence: string;
  preserved_balance: number;
  unit_compatible: boolean;
  unit_conversion_reason: string | null;
  warehouse_eligible: boolean;
  projection_eligible: boolean;
  date_status: StockProjectionDateStatus;
  date_semantics: string;
};

export type SafetyStockPurchaseCoverage = {
  status: PurchaseCoverageStatus;
  deficit_quantity: number;
  eligible_open_quantity: number;
  remaining_to_buy: number;
  open_order_count: number;
  eligible_order_count: number;
  next_expected_delivery_date: string | null;
  incompatible_unit_order_count: number;
  warnings: string[];
};

export type SafetyStockCollectionBlock<T, S = undefined> = {
  items: T[];
  total: number;
  summary?: S;
};

export type SafetyStockCommitmentsSummary = {
  eligible_open_quantity: number;
  next_commitment_date: string | null;
  incompatible_unit_commitment_count: number;
  eligible_warehouses: string[];
  warnings: string[];
};

export type SafetyStockProjectionLedgerEntry = {
  sequence: number;
  event_date: string | null;
  date_status: StockProjectionDateStatus;
  date_semantics: string;
  origin: StockProjectionOrigin;
  origin_label: string;
  reference: string;
  warehouse: string;
  movement: number;
  inflow: number;
  outflow: number;
  running_balance: number;
  unit_compatible: boolean;
  projection_eligible: boolean;
};

export type SafetyStockProjectionSummary = {
  as_of_date: string;
  initial_balance: number;
  safety_stock: number;
  eligible_purchase_quantity: number;
  eligible_commitment_quantity: number;
  final_projected_balance: number;
  final_balance_after_safety: number;
  minimum_projected_balance: number;
  first_shortage_date: string | null;
  projected_remaining_to_buy: number;
  status: StockProjectionStatus;
  eligible_warehouses: string[];
  warnings: string[];
};

export type SafetyStockItemDetails = {
  product: {
    product_code: string;
    product_description: string;
    product_type: string;
    unit: string;
    secondary_unit: string;
    conversion_factor: number | null;
    conversion_type: string;
    product_group: string;
    branch: string;
    blocked: boolean;
    status: SafetyStockStatus;
  };
  stock: {
    safety_stock: number;
    available_stock: number;
    primary_stock: number;
    warehouse_50_stock: number;
    warehouse_98_stock: number;
    warehouse_99_stock: number;
    work_in_process_stock: number;
    work_in_process_committed: number;
    work_in_process_available: number;
    deficit_quantity: number;
  };
  purchase_coverage: SafetyStockPurchaseCoverage;
  open_purchase_orders: SafetyStockCollectionBlock<SafetyStockOpenPurchaseOrder>;
  open_commitments: SafetyStockCollectionBlock<
    SafetyStockOpenCommitment,
    SafetyStockCommitmentsSummary
  >;
  stock_projection: SafetyStockCollectionBlock<
    SafetyStockProjectionLedgerEntry,
    SafetyStockProjectionSummary
  >;
};

export type SafetyStockLinkedSupplier = {
  product_code: string;
  supplier_code: string;
  supplier_store: string;
  /** Partnumber do produto no fornecedor (SA5 `A5_CODPRF`). */
  supplier_part_number: string;
  trade_name: string;
  legal_name: string;
  document: string;
  has_last_purchase: boolean;
  last_purchase_date: string | null;
  last_unit_price: number | null;
  last_quantity: number | null;
  last_total_value: number | null;
  last_invoice_number: string | null;
  last_invoice_series: string | null;
};

export type SafetyStockLinkedSuppliersData = SafetyStockCollectionBlock<SafetyStockLinkedSupplier>;

export type SafetyStockSupplierPriceHistoryPoint = {
  branch: string;
  purchase_date: string | null;
  issue_date: string | null;
  supplier_code: string;
  supplier_store: string;
  supplier_name: string;
  unit_price: number;
  quantity: number;
  total_value: number;
  invoice_number: string;
  invoice_series: string;
};

export type SafetyStockSupplierPriceHistorySummary = {
  total_purchases: number;
  min_unit_price: number | null;
  max_unit_price: number | null;
  first_unit_price: number | null;
  last_unit_price: number | null;
  variation_percent: number | null;
};

export type SafetyStockSupplierPriceHistoryData = {
  product_code: string;
  branch: string;
  supplier_code: string;
  supplier_store: string;
  date_start: string;
  date_end_exclusive: string;
  items: SafetyStockSupplierPriceHistoryPoint[];
  total: number;
  summary: SafetyStockSupplierPriceHistorySummary;
};

export type SafetyStockQueryParams = {
  branch: string;
  includeBlocked: boolean;
  productGroup: string;
  unit: string;
  search: string;
  status: SafetyStockStatus | "";
  includeWithoutSafetyStock: boolean;
  sortBy: SafetyStockSortField;
  sortDirection: SortDirection;
};

export const DEFAULT_QUERY_PARAMS: SafetyStockQueryParams = {
  branch: "",
  includeBlocked: false,
  productGroup: "",
  unit: "",
  search: "",
  status: "below_safety_stock",
  includeWithoutSafetyStock: false,
  sortBy: "product_code",
  sortDirection: "asc",
};

export const MAX_PAGE_SIZE = 200;
export const DEFAULT_PAGE_SIZE = 50;
export const PAGE_SIZE_OPTIONS = [25, 50, 100] as const;

export const SORT_FIELD_OPTIONS: { value: SafetyStockSortField; label: string }[] = [
  { value: "product_code", label: "Código" },
  { value: "product_description", label: "Descrição" },
  { value: "product_group", label: "Grupo" },
  { value: "unit", label: "Unidade" },
  { value: "safety_stock", label: "Estoque de segurança" },
  { value: "primary_stock", label: "Saldo" },
  { value: "work_in_process_stock", label: "Estoque em processo" },
  { value: "deficit_quantity", label: "Déficit" },
  { value: "status", label: "Situação" },
];
