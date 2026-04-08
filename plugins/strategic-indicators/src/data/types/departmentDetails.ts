export type DepartmentIndicator = {
  id: string;
  name: string;
  weightPct: number;
  goalLabel: string;
  goalValue: number;
  goalPeriodicity: string;
  strategicDescription: string;
  scopeType: string;
  realized: Record<string, number>;
  score: number;
  gap: number;
  trend: "up" | "down" | "stable";
};

export type DepartmentUnit = {
  unitId: string;
  unitName: string;
  score: number;
  classification: string;
};

export type DepartmentDetails = {
  id: string;
  name: string;
  shortName: string;
  weightInIgd: number;
  score: number;
  classification: string;
  contribution: number;
  aggregationMode: string;
  strategicSummary: string;
  variation: {
    value: number;
    direction: string;
  };
  units: DepartmentUnit[];
  indicators: DepartmentIndicator[];
};

export type StrategicIndicatorsDepartmentDetailsResponse = {
  id: string;
  name: string;
  short_name: string;
  weight_pct: number;
  score: number;
  classification: string;
  contribution: number;
  aggregation_mode: string;
  strategic_summary: string;
  variation: {
    value: number;
    direction: string;
  };
  units: Array<{
    unit_id: string;
    unit_name: string;
    score: number;
    classification: string;
  }>;
  indicators: Array<{
    id: string;
    name: string;
    weight_pct: number;
    goal_label: string;
    goal_value: number;
    goal_periodicity: string;
    strategic_description: string;
    scope_type: string;
    realized: Record<string, number>;
    score: number;
    gap: number;
    trend: string;
  }>;
  errors?: Array<{
    department_id: string;
    source: string;
    message: string;
  }>;
  partial_success?: boolean;
};

export type DepartmentDetailsViewData = DepartmentDetails;