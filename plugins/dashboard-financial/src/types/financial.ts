import type { DashboardGoalFields } from "../utils/goalDisplay";

export type FinancialFilterParams = {
  start_date?: string;
  end_date?: string;
  branch?: string;
};

export type RolData = {
  branch: string;
  start_date: string;
  end_date: string;
  gross_revenue: number;
  other_values: number;
  items_without_tes: number;
  returns: number;
  discounts: number;
  icms: number;
  iss: number;
  pis: number;
  cofins: number;
  ipi_separated: number;
  rol_taxes: number;
  rol: number;
  rol_with_ipi: number;
  financial_titles: number;
  financial_balance: number;
};

export type FinancialBranchMetric = {
  branch: string;
};

export type EbitdaBranchRow = FinancialBranchMetric & {
  ebitda_value: number;
  rol_with_ipi: number;
  ebitda_over_rol_pct: number;
};

export type EbitdaPctData = DashboardGoalFields & {
  branch: string | null;
  start_date: string;
  end_date: string;
  ebitda_value?: number;
  rol_with_ipi?: number;
  ebitda_over_rol_pct: number;
  branches?: EbitdaBranchRow[];
};

export type FixedCostBranchRow = FinancialBranchMetric & {
  fixed_cost_value: number;
  rol_with_ipi: number;
  fixed_cost_over_rol_pct: number;
};

export type FixedCostPctData = DashboardGoalFields & {
  branch: string | null;
  start_date: string;
  end_date: string;
  fixed_cost_value?: number;
  rol_with_ipi?: number;
  fixed_cost_over_rol_pct: number;
  branches?: FixedCostBranchRow[];
};

export type PmrBranchRow = FinancialBranchMetric & {
  pmr_days: number;
};

export type PmrData = DashboardGoalFields & {
  branch: string | null;
  start_date: string;
  end_date: string;
  pmr_days: number;
  branches?: PmrBranchRow[];
};
