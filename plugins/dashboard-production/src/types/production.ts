import type { ChartGranularity } from "./chart";
import type { DashboardGoalFields } from "../utils/goalDisplay";

export type ProductionFilterParams = {
  start_date?: string;
  end_date?: string;
  branch?: string;
  granularity?: ChartGranularity;
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
