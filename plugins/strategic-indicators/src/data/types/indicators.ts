export type IndicatorViewItem = {
  id: string;
  name: string;
  departmentId: string;
  departmentName: string;
  weightPct: number;
  goalLabel: string;
  goalValue: number;
  goalPeriodicity: string;
  value: number;
  score: number;
  gap: number;
  trend: "up" | "down" | "stable";
  classification: string;
  source: string;
};

export type IndicatorFetchErrorViewItem = {
  departmentId: string;
  source: string;
  message: string;
};

export type StrategicIndicatorsResponse = {
  items: Array<{
    department_id: string;
    department_name: string;
    indicator_id: string;
    indicator_name: string;
    weight_pct: number;
    goal_label: string;
    goal_value: number;
    goal_periodicity: string;
    scope_type: string;
    value: number;
    score: number;
    gap: number;
    trend: string;
    classification: string;
    source: string;
  }>;
  errors?: Array<{
    department_id: string;
    source: string;
    message: string;
  }>;
  partial_success?: boolean;
};