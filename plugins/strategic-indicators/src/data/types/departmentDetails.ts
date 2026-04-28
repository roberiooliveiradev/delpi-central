export type TrendDirection = "up" | "down" | "stable";

export type GoalMode = "standard" | "monthly_curve";

export type PerformanceDirection =
  | "higher_is_better"
  | "lower_is_better";

export type IndicatorValueUnit =
  | "percent"
  | "currency"
  | "ppm"
  | "days"
  | "hours"
  | "count"
  | "ratio"
  | "months"
  | string;

export type MonthlyTargetItem = {
  month_number: number;
  target_value: number;
};

export type DepartmentIndicator = {
  id: string;
  name: string;
  weightPct: number;
  goalLabel: string;
  goalValue: number;
  goalPeriodicity: string;
  goalMode: GoalMode;
  monthlyTargets: MonthlyTargetItem[];
  strategicDescription: string;
  scopeType: string;
  performanceDirection: PerformanceDirection;
  realized: Record<string, number>;
  score: number;
  gap: number;
  trend: TrendDirection;
  valueUnit: IndicatorValueUnit | null;
  valuePrefix: string | null;
  valueSuffix: string | null;
  valueDecimals: number;
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
    goal_mode: GoalMode;
    monthly_targets: MonthlyTargetItem[];
    strategic_description: string;
    scope_type: string;
    performance_direction: PerformanceDirection;
    realized: Record<string, number>;
    score: number;
    gap: number;
    trend: string;
    value_unit?: IndicatorValueUnit | null;
    value_prefix?: string | null;
    value_suffix?: string | null;
    value_decimals?: number | null;
  }>;
  errors?: Array<{
    department_id: string;
    source: string;
    message: string;
  }>;
  partial_success?: boolean;
};

export type DepartmentDetailsViewData = DepartmentDetails;