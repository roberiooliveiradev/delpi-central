export type TrendDirection = "up" | "down" | "stable";

export type GoalMode = "standard" | "monthly_curve";

export type PerformanceDirection =
  | "higher_is_better"
  | "lower_is_better";

export type MonthlyTargetItem = {
  month_number: number;
  target_value: number;
};

export type IndicatorViewItem = {
  id: string;
  name: string;
  departmentId: string;
  departmentName: string;
  weightPct: number;
  goalLabel: string;
  goalValue: number;
  goalPeriodicity: string;
  goalMode: GoalMode;
  monthlyTargets: MonthlyTargetItem[];
  value: number;
  score: number;
  gap: number;
  trend: TrendDirection;
  classification: string;
  scopeType: string;
  performanceDirection: PerformanceDirection;
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
    goal_mode: GoalMode;
    monthly_targets: MonthlyTargetItem[];
    scope_type: string;
    performance_direction: PerformanceDirection;
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