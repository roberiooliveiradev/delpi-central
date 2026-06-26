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
  rol_with_ipi: number;
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
