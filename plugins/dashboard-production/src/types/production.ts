import type { ChartGranularity } from "./chart";
import type { DashboardGoalFields } from "../utils/goalDisplay";

export type ProductionFilterParams = {
  start_date?: string;
  end_date?: string;
  branch?: string;
  granularity?: ChartGranularity;
};

export type ProductionOrderProductType = "PA" | "PI";

export type DirectLaborCostPctData = DashboardGoalFields & {
  direct_labor_cost_pct: number | null;
};

export type ProductionCostPctData = DashboardGoalFields & {
  production_cost_pct: number | null;
};

export type DepreciationPctData = DashboardGoalFields & {
  depreciation_pct: number | null;
};

export type OeePctData = DashboardGoalFields & {
  overall_equipment_effectiveness_pct: number | null;
};

export type OtdPctData = DashboardGoalFields & {
  on_time_delivery_pct: number | null;
};

export type ProductionOeeSeriesPoint = {
  periodo: string;
  sort_key: string;
  date_start: string;
  date_end: string;
  oee_filial_01: number | null;
  oee_filial_02: number | null;
};

export type ProductionOeeSeriesData = {
  granularity: string;
  truncated: boolean;
  branch: string | null;
  points: ProductionOeeSeriesPoint[];
};

export type ProductionOtdSeriesPoint = {
  periodo: string;
  sort_key: string;
  date_start: string;
  date_end: string;
  otd_filial_01: number | null;
  otd_filial_02: number | null;
};

export type ProductionOtdSeriesData = {
  granularity: string;
  truncated: boolean;
  branch: string | null;
  points: ProductionOtdSeriesPoint[];
};

export type ProductionOtdOrderStatus = "on_time" | "late";

export type ProductionOtdOrderItem = {
  branch: string;
  production_order: string;
  order_number: string;
  order_item: string;
  product_code: string;
  product_description: string;
  due_date: string;
  finish_date: string;
  days_diff: number;
  status: ProductionOtdOrderStatus;
};

export type ProductionOtdOrdersPage = {
  items: ProductionOtdOrderItem[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type ProductionOtdSummary = DashboardGoalFields & {
  total_ops_finished: number;
  on_time_ops: number;
  late_ops: number;
  on_time_delivery_pct: number | null;
  late_percentage: number;
};

export type ProductionOtdData = {
  branch: string;
  start_date: string;
  end_date: string;
  summary: ProductionOtdSummary;
  orders: ProductionOtdOrdersPage;
};

export type ProductionOtdParams = ProductionFilterParams & {
  status?: ProductionOtdOrderStatus | "";
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
};

export type ProductionOrderByOpParams = {
  branch?: string;
  productType?: ProductionOrderProductType;
  linkedSortBy?: string;
  linkedSortDir?: "asc" | "desc";
};

export type ProductionOrderOtdStatus = "open" | "on_time" | "late";

export type ProductionOrderDetail = {
  branch: string;
  production_order: string;
  order_number: string;
  order_item: string;
  order_sequence: string;
  product_code: string;
  product_description: string;
  product_type: string;
  unit: string;
  product_group: string;
  warehouse: string;
  planned_qty: number | null;
  produced_qty: number | null;
  priority: string;
  order_status: string;
  observation: string;
  issue_date: string | null;
  planned_start_date: string | null;
  due_date: string | null;
  finish_date: string | null;
  days_diff: number | null;
  otd_status: ProductionOrderOtdStatus;
};

export type ProductionOrderByOpData = {
  order: ProductionOrderDetail;
  linked_orders: ProductionOrderDetail[];
  link_summary: {
    order_number: string;
    link_field: string;
    total_pi_orders: number;
    on_time_ops: number;
    late_ops: number;
    open_ops: number;
  };
  related_routes: {
    product_detail: string;
    product_summary: string;
    product_guide: string;
    product_stock: string;
    product_production_status: string;
  };
};

export type ProductStockItem = {
  branch?: string;
  warehouse?: string;
  balance?: number | null;
  [key: string]: unknown;
};

export type ProductPriceItem = {
  table?: string;
  price?: number | null;
  [key: string]: unknown;
};

export type ProductSummaryData = {
  product: Record<string, unknown>;
  stock: ProductStockItem[];
  prices: ProductPriceItem[];
};

export type ProductStructureNode = {
  code?: string;
  product_code?: string;
  description?: string;
  type?: string;
  quantity?: number | null;
  components?: ProductStructureNode[];
  items?: ProductStructureNode[];
  [key: string]: unknown;
};

export type ProductStructureData = {
  root?: ProductStructureNode;
  items?: ProductStructureNode[];
  total?: number;
  page?: number;
  page_size?: number;
  total_pages?: number;
};

export type IntermediateProductionOrderRow = {
  key: string;
  level: number;
  product_code: string;
  description: string;
  product_type: string;
  branch: string;
  production_order: string;
  order_number: string;
  order_item: string;
  due_date: string | null;
  finish_date: string | null;
  days_diff: number | null;
  otd_status: ProductionOrderOtdStatus;
  planned_qty: number | null;
  produced_qty: number | null;
  production_started: boolean;
};
