export type SuppliesFilterParams = {
  start_date?: string;
  end_date?: string;
  branch?: string;
  location?: string;
  top_limit?: number;
};

export type CpvSummary = {
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
  cpv_total?: number;
  total_quantity?: number;
  label?: string;
  name?: string;
  product_code?: string;
  product_description?: string;
  value?: number;
};

export type CpvData = {
  branch: string;
  start_date: string;
  end_date: string;
  summary: CpvSummary;
  by_cfop: CpvBreakdownItem[];
  by_tm: CpvBreakdownItem[];
  top_products: CpvBreakdownItem[];
};

export type OtdSummary = {
  total_lines: number;
  on_time_lines: number;
  late_lines: number;
  otd_percentage: number;
  late_percentage: number;
};

export type OtdMonthlyItem = {
  month?: string;
  period?: string;
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

export type OtdData = {
  branch: string;
  start_date: string;
  end_date: string;
  summary: OtdSummary;
  monthly_breakdown: OtdMonthlyItem[];
  top_late_suppliers: LateSupplierItem[];
};

export type StockValueSummary = {
  total_stock_value: number;
  total_stock_quantity: number;
  total_records: number;
  total_products: number;
  total_locations: number;
  average_unit_value: number;
};

export type StockValueByLocation = {
  location?: string;
  total_stock_value?: number;
  total_stock_quantity?: number;
};

export type StockValueData = {
  branch: string;
  location: string;
  summary: StockValueSummary;
  by_location: StockValueByLocation[];
};

export type InventoryTurnoverSummary = {
  inventory_turnover_months: number;
  inventory_turnover_times: number;
  total_stock_value: number;
  cpv_total: number;
  cpv_average_monthly: number;
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
};
