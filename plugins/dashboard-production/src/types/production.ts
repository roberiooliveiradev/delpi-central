import type { DashboardGoalFields } from "../utils/goalDisplay";

export type ProductionFilterParams = {
  start_date?: string;
  end_date?: string;
  branch?: string;
};

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
