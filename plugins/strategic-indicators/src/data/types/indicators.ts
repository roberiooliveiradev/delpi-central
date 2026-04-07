export type StrategicIndicatorItemApi = {
  department_id: string;
  department_name: string;
  indicator_id: string;
  indicator_name: string;
  weight_pct: number;
  goal_2026: string;
  scope_type: "per_unit" | "consolidated" | "matrix_only" | "branch_only";
  value: number;
  score: number;
  gap: number;
  trend: "up" | "down" | "stable";
  classification: string;
  source: string;
};

export type StrategicIndicatorsResponse = {
  items: StrategicIndicatorItemApi[];
};

export type IndicatorViewItem = {
  id: string;
  departmentId: string;
  departmentName: string;
  name: string;
  weightPct: number;
  goal2026: string;
  value: number;
  score: number;
  gap: number;
  trend: "up" | "down" | "stable";
  classification: string;
  source: string;
};