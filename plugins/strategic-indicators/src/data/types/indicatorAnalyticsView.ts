export type IndicatorAnalyticsStatus =
  | "success"
  | "info"
  | "warning"
  | "danger";

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
  currentValue: number;
  score: number;
  gap: number;
  trend: "up" | "down" | "stable";
  status: IndicatorAnalyticsStatus;
  source: string;
};