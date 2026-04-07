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
  goal2026: string;
  currentValue: number;
  score: number;
  gap: number;
  trend: "up" | "down" | "stable";
  status: IndicatorAnalyticsStatus;
  source: string;
};