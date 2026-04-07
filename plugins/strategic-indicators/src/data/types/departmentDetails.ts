export type DepartmentDetailsVariationApi = {
  value: number;
  direction: "up" | "down" | "stable";
};

export type DepartmentUnitScoreApi = {
  unit_id: string;
  unit_name: string;
  score: number;
  classification: string;
};

export type DepartmentIndicatorDetailsApi = {
  id: string;
  name: string;
  weight_pct: number;
  goal_2026: string;
  strategic_description: string;
  scope_type: "per_unit" | "consolidated" | "matrix_only" | "branch_only";
  realized: Record<string, number>;
  score: number;
  gap: number;
  trend: "up" | "down" | "stable";
};

export type StrategicIndicatorsDepartmentDetailsResponse = {
  id: string;
  name: string;
  short_name: string;
  weight_pct: number;
  score: number;
  classification: string;
  contribution: number;
  aggregation_mode: "average_of_units" | "consolidated" | "mixed_scope";
  strategic_summary: string;
  variation: DepartmentDetailsVariationApi;
  units: DepartmentUnitScoreApi[];
  indicators: DepartmentIndicatorDetailsApi[];
};

export type DepartmentIndicatorViewItem = {
  id: string;
  name: string;
  weightPct: number;
  goal2026: string;
  strategicDescription: string;
};

export type DepartmentDetailsViewData = {
  id: string;
  name: string;
  shortName: string;
  weightInIgd: number;
  score: number;
  classification: string;
  strategicSummary: string;
  aggregationMode: "average_of_units" | "consolidated" | "mixed_scope";
  contribution: number;
  variation: {
    value: number;
    direction: "up" | "down" | "stable";
  };
  units: {
    unitId: string;
    unitName: string;
    score: number;
    classification: string;
  }[];
  indicators: DepartmentIndicatorViewItem[];
};