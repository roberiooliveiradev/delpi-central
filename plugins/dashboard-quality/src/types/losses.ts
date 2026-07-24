import type { DashboardGoalFields } from "../utils/goalDisplay";

export type CostPctSummary = DashboardGoalFields & {
  branch?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  scrap_cost?: number | null;
  scrap_cost_pct?: number | null;
  rework_cost?: number | null;
  rework_cost_pct?: number | null;
  rol?: number | null;
  rol_with_ipi?: number | null;
  quantity?: number | null;
  occurrences?: number | null;
};
