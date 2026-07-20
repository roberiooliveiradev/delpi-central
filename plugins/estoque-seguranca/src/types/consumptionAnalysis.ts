import type { SortDirection } from "./safetyStock";

export type ConsumptionAnalysisStatus =
  | "below_suggested"
  | "above_suggested"
  | "adequate"
  | "inconsistent_data";

export type ConsumptionAnalysisSortField =
  | "product_code"
  | "product_description"
  | "product_group"
  | "unit"
  | "safety_stock"
  | "suggested_safety_stock"
  | "difference_quantity"
  | "average_daily_consumption"
  | "lead_time_days"
  | "coverage_business_days"
  | "period_consumption"
  | "analysis_status";

export type ConsumptionAnalysisQueryParams = {
  branch: string;
  includeBlocked: boolean;
  productGroup: string;
  unit: string;
  search: string;
  analysisStatus: ConsumptionAnalysisStatus | "";
  sortBy: ConsumptionAnalysisSortField;
  sortDirection: SortDirection;
};

export type StatusDistributionItem = {
  status: ConsumptionAnalysisStatus;
  count: number;
};

export type ConsumptionAnalysisSummaryData = {
  analyzed_items: number;
  below_suggested: number;
  above_suggested: number;
  adequate: number;
  inconsistent_data: number;
  net_difference_quantity: number;
  branch: string;
  period_start: string;
  period_end: string;
  period_calendar_days: number;
  period_business_days: number;
  consumption_warehouse: string;
  consumption_movement_type: string;
  status_distribution: StatusDistributionItem[];
};

export type ConsumptionAnalysisItem = {
  product_code: string;
  product_description: string;
  product_type: string;
  unit: string;
  product_group: string;
  branch: string;
  blocked: boolean;
  safety_stock: number;
  suggested_safety_stock: number;
  difference_quantity: number;
  difference_percent: number | null;
  available_stock: number;
  primary_stock: number;
  warehouse_98_stock: number;
  warehouse_99_stock: number;
  period_consumption: number;
  average_daily_consumption: number;
  lead_time_days: number;
  lead_time_business_days: number;
  coverage_business_days: number | null;
  movement_count: number;
  first_movement_date: string | null;
  last_movement_date: string | null;
  analysis_status: ConsumptionAnalysisStatus;
  quality_warnings: string[];
  has_inconsistent_data: boolean;
  period_start: string;
  period_end: string;
  period_calendar_days: number;
  period_business_days: number;
};

export type ConsumptionAnalysisItemsData = {
  items: ConsumptionAnalysisItem[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  sort_by: ConsumptionAnalysisSortField;
  sort_direction: SortDirection;
  period_start: string;
  period_end: string;
  period_calendar_days: number;
  period_business_days: number;
};

export type MonthlyConsumptionPoint = {
  year_month: string;
  year_month_label: string;
  consumption_quantity: number;
  movement_count: number;
};

export type AnnualComparisonMonth = {
  month: number;
  month_label: string;
  values_by_year: Record<string, number | null>;
};

export type AnnualComparisonData = {
  years: string[];
  items: AnnualComparisonMonth[];
  total: number;
  period_start: string;
  period_end: string;
};

export type CalculationMemory = {
  formula: string;
  average_daily_consumption_formula: string;
  period_consumption: number;
  period_business_days: number;
  average_daily_consumption: number;
  lead_time_days: number;
  lead_time_business_days: number;
  suggested_safety_stock: number;
  current_safety_stock: number;
  available_stock: number;
  coverage_business_days: number | null;
  consumption_filters: {
    warehouse: string;
    movement_type: string;
    requires_production_order: boolean;
    signed_quantity: boolean;
  };
  quality_warnings: string[];
};

export type ConsumptionAnalysisItemDetails = {
  item: ConsumptionAnalysisItem;
  monthly_consumption: {
    items: MonthlyConsumptionPoint[];
    total: number;
  };
  annual_comparison?: AnnualComparisonData;
  calculation_memory: CalculationMemory;
  period_start: string;
  period_end: string;
};

export const DEFAULT_ANALYSIS_QUERY_PARAMS: ConsumptionAnalysisQueryParams = {
  branch: "",
  includeBlocked: false,
  productGroup: "",
  unit: "",
  search: "",
  analysisStatus: "below_suggested",
  sortBy: "difference_quantity",
  sortDirection: "asc",
};

export const ANALYSIS_SORT_FIELD_OPTIONS: {
  value: ConsumptionAnalysisSortField;
  label: string;
}[] = [
  { value: "difference_quantity", label: "Diferença (atual − sugerido)" },
  { value: "suggested_safety_stock", label: "Sugerido" },
  { value: "safety_stock", label: "Estoque atual" },
  { value: "average_daily_consumption", label: "Consumo diário" },
  { value: "lead_time_days", label: "Lead time (dias)" },
  { value: "coverage_business_days", label: "Cobertura (dias úteis)" },
  { value: "period_consumption", label: "Consumo do período" },
  { value: "product_code", label: "Código" },
  { value: "product_description", label: "Descrição" },
  { value: "product_group", label: "Grupo" },
  { value: "unit", label: "Unidade" },
  { value: "analysis_status", label: "Situação" },
];
