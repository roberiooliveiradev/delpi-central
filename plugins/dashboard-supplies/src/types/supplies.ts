import type { DashboardGoalFields } from "../utils/goalDisplay";

export type SuppliesFilterParams = {
  start_date?: string;
  end_date?: string;
  branch?: string;
  location?: string;
  top_limit?: number;
};

export type CpvSummary = DashboardGoalFields & {
  cpv_total: number;
  rol: number;
  cpv_percentage: number;
  total_movements: number;
  total_quantity: number;
  average_cost_per_movement: number;
  average_cost_per_unit: number;
};

export type CpvBreakdownItem = {
  cfop?: string;
  tm?: string;
  tes_description?: string;
  cpv_total?: number;
  total_quantity?: number;
  total_movements?: number;
  product_code?: string;
  product_description?: string;
  document?: string;
};

export type CpvData = {
  branch: string;
  start_date: string;
  end_date: string;
  summary: CpvSummary;
  by_cfop: CpvBreakdownItem[];
  by_tm: CpvBreakdownItem[];
  top_products: CpvBreakdownItem[];
  top_documents: CpvBreakdownItem[];
};

export type OtdSummary = DashboardGoalFields & {
  total_lines: number;
  on_time_lines: number;
  late_lines: number;
  otd_percentage: number;
  late_percentage: number;
};

export type OtdMonthlyItem = {
  month?: string | number;
  year?: string | number;
  month_date?: string;
  otd_percentage?: number;
  total_lines?: number;
  on_time_lines?: number;
  late_lines?: number;
};

export type LateSupplierItem = {
  supplier_code?: string;
  supplier_name?: string;
  supplier?: string;
  late_lines?: number;
  total_lines?: number;
  late_percentage?: number;
};

export type LateDeliveryItem = {
  branch?: string;
  supplier_code?: string;
  supplier_name?: string;
  document?: string;
  order_number?: string;
  order_item?: string;
  product_code?: string;
  product_description?: string;
  quantity?: number;
  expected_delivery_date?: string;
  receipt_entry_date?: string;
  days_diff?: number;
};

export type OtdData = {
  branch: string;
  start_date: string;
  end_date: string;
  summary: OtdSummary;
  monthly_breakdown: OtdMonthlyItem[];
  top_late_suppliers: LateSupplierItem[];
  late_deliveries: LateDeliveryItem[];
};

export type StockValueSummary = DashboardGoalFields & {
  total_stock_value: number;
  total_stock_quantity: number;
  total_records: number;
  total_products: number;
  total_locations: number;
  average_unit_value: number;
};

export type StockValueByLocation = {
  location?: string;
  branch?: string;
  total_stock_value?: number;
  total_stock_quantity?: number;
  closing_base_date?: string | null;
  closing_base_value?: number;
  bridge_value?: number;
  period_net_value?: number;
  official_closure_date?: string | null;
  official_closure_value?: number | null;
  official_closure_available?: boolean;
  official_closure_on_period_end?: boolean;
};

export type StockTopProduct = {
  product_code?: string;
  product_description?: string;
  location?: string;
  total_stock_value?: number;
  total_stock_quantity?: number;
};

export type StockValueEstimation = {
  enabled: boolean;
  method: string;
  stock_method?: string;
  stock_method_resolved?: string;
  start_date: string;
  end_date?: string;
  end_date_exclusive: string;
  note: string;
  closing_base_date?: string | null;
  closing_base_value?: number;
  bridge_value?: number;
  period_net_value?: number;
  official_closure_available?: boolean;
  official_closure_date?: string | null;
  official_closure_value?: number | null;
  official_closure_on_period_end?: boolean;
  data_quality_warning?: string;
  inventory_register?: {
    em_estoque_value?: number;
    em_processo_proxy_value?: number;
    em_processo_proxy_method?: string;
    process_locations?: string[];
    total_geral_proxy_value?: number;
    snapshot_at_query_time?: boolean;
    period_end_requested?: string;
    by_branch?: Array<{
      branch?: string;
      em_estoque_value?: number;
      em_processo_proxy_value?: number;
    }>;
  };
  wip_proxy?: {
    enabled: boolean;
    total_wip_value?: number;
    method?: string;
    process_locations?: string[];
    note?: string;
  };
};

export type StockValueData = {
  branch: string;
  location: string;
  summary: StockValueSummary;
  by_branch: StockValueByLocation[];
  by_location: StockValueByLocation[];
  top_products: StockTopProduct[];
  estimation?: StockValueEstimation;
};

export type InventoryTurnoverSummary = DashboardGoalFields & {
  inventory_turnover_months: number;
  inventory_turnover_times: number;
  total_stock_value: number;
  cpv_total: number;
  cpv_average_monthly: number;
};

export type NegotiationSavingsSummary = DashboardGoalFields & {
  total_savings: number | null;
};

export type NegotiationSavingsBranchItem = {
  branch?: string;
  total_savings?: number | null;
};

export type NegotiationSavingsEntry = {
  branch?: string;
  date?: string;
  savings_amount?: number;
};

export type NegotiationSavingsData = {
  start_date?: string;
  end_date?: string;
  branch?: string | null;
  total_savings?: number | null;
  summary: NegotiationSavingsSummary;
  branches: NegotiationSavingsBranchItem[];
  entries: NegotiationSavingsEntry[];
};

export type InventoryTurnoverData = {
  branch: string;
  location: string;
  start_date: string;
  end_date: string;
  summary: InventoryTurnoverSummary;
  calculation_context: {
    calculation_mode: string;
    idd_period_valid: boolean;
    strict_idd_period: boolean;
    period_reference: number;
  };
  stock_context: DashboardGoalFields & {
    total_stock_value: number;
    total_stock_quantity: number;
    total_records: number;
    total_products: number;
    total_locations: number;
    average_unit_value: number;
  };
  cpv_context: {
    cpv_total: number;
    total_movements: number;
    total_quantity: number;
    cpv_average_monthly: number;
  };
  stock_estimation?: StockValueEstimation;
};

export type NonMovingTurnoverStatus =
  | "WITH_CONSUMPTION"
  | "NO_CONSUMPTION_12M"
  | "NO_CONSUMPTION_IN_PERIOD"
  | "INSUFFICIENT_HISTORY";

export type NonMovingStockReference = {
  consumption_window_start: string;
  consumption_window_end: string;
  window_kind: "rolling_12m" | "custom_period";
  valuation_reference: string;
  product_type: string;
  branches: string[];
  warehouses: string[];
};

export type NonMovingStockStatusBreakdown = {
  turnover_status: NonMovingTurnoverStatus | string;
  product_count: number;
  stock_value: number;
  blocked_stock_value: number;
};

export type NonMovingStockBranchBreakdown = {
  branch: string;
  product_count: number;
  eligible_stock_value: number;
  no_consumption_stock_value: number;
  insufficient_history_stock_value: number;
  blocked_stock_value: number;
};

export type NonMovingStockSummaryData = {
  reference: NonMovingStockReference;
  summary: {
    eligible_stock_value: number;
    evaluable_stock_value: number;
    no_consumption_stock_value: number;
    with_consumption_stock_value: number;
    insufficient_history_stock_value: number;
    non_moving_percentage: number | null;
    coverage_percentage: number | null;
    blocked_stock_value: number;
    blocked_no_consumption_stock_value: number;
    status: string;
    unavailable_reason: string | null;
  };
  counts: {
    eligible_products: number;
    with_consumption: number;
    no_consumption: number;
    insufficient_history: number;
    blocked_products: number;
    /** Itens (produto×filial×armazém) com custo médio zero — valor não mensurável. */
    zero_cost_items: number;
  };
  by_status: NonMovingStockStatusBreakdown[];
  by_branch: NonMovingStockBranchBreakdown[];
};

export type NonMovingStockItem = {
  branch: string;
  product_code: string;
  description: string | null;
  unit_of_measure: string | null;
  warehouse: string;
  quantity: number;
  unit_cost: number;
  stock_value: number;
  blocked: boolean;
  turnover_status: NonMovingTurnoverStatus | string;
  last_effective_utilization: string | null;
  last_utilization_in_window: string | null;
};

export type InventoryAccuracyReference = {
  reference_month: string | null;
  period_start: string;
  period_end_exclusive: string;
  period_kind: "last_closed_month" | "month" | "custom_period";
  period_closed: boolean;
  branches: string[];
};

export type InventoryAccuracyBranchBreakdown = {
  branch: string;
  valid_count_total: number;
  evaluable_count_total: number;
  accurate_count: number;
  divergent_count: number;
  excluded_count: number;
  shortage_value_total: number;
  surplus_value_total: number;
};

export type InventoryAccuracySummaryData = {
  reference: InventoryAccuracyReference;
  summary: {
    valid_count_total: number;
    evaluable_count_total: number;
    accurate_count: number;
    divergent_count: number;
    accuracy_percentage: number | null;
    coverage_percentage: number | null;
    shortage_value_total: number;
    surplus_value_total: number;
    comparison_source: string;
    status: string;
    unavailable_reason: string | null;
  };
  exclusions: {
    pending_processing: number;
    cancelled: number;
  };
  by_branch: InventoryAccuracyBranchBreakdown[];
};

export type InventoryAccuracyOutcome =
  | "accurate"
  | "divergent"
  | "excluded";

export type InventoryAccuracyItem = {
  branch: string;
  product_code: string;
  description: string | null;
  unit_of_measure: string | null;
  blocked: boolean;
  warehouse: string;
  count_date: string | null;
  counted_quantity: number;
  theoretical_quantity: number;
  divergence_quantity: number;
  shortage_quantity: number;
  surplus_quantity: number;
  shortage_value: number;
  surplus_value: number;
  adjustment_rows: number;
  physical_lines: number;
  inventory_document: string | null;
  count_status: string;
  outcome: InventoryAccuracyOutcome | string;
  exclusion_reason: string | null;
};

export type SuppliesPagedResponse<T> = {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  sort?: string;
  reference?: Record<string, unknown>;
};
