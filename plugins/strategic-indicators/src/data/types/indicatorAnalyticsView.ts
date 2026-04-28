export type IndicatorAnalyticsStatus =
  | "success"
  | "info"
  | "warning"
  | "danger";

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

export type MonthlyTargetViewItem = {
  monthNumber: number;
  targetValue: number;
};

export type IndicatorAnalyticsViewItem = {
  id: string;
  departmentId: string;
  departmentName: string;
  indicatorName: string;
  strategicDescription: string;
  weightPct: number;
  goalLabel: string;
  goalValue: number;
  goalPeriodicity: string;
  goalMode: GoalMode;
  monthlyTargets: MonthlyTargetViewItem[];
  performanceDirection: PerformanceDirection;
  currentValue: number;
  score: number;
  gap: number;
  trend: "up" | "down" | "stable";
  status: IndicatorAnalyticsStatus;
  source: string;

  valueUnit: IndicatorValueUnit | null;
  valuePrefix: string | null;
  valueSuffix: string | null;
  valueDecimals: number;
};