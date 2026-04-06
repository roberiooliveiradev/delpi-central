export type ExecutiveSummaryApiVariation = {
  value: number;
  direction: "up" | "down" | "stable";
  vs_label: string;
};

export type ExecutiveSummaryApiDepartment = {
  id: string;
  name: string;
  short_name: string;
  weight_pct: number;
  score: number;
  contribution: number;
  trend: "up" | "down" | "stable";
  strategic_summary: string;
  key_indicators: string[];
  executive_goal: string;
};

export type ExecutiveSummaryApiAlert = {
  title: string;
  severity: "high" | "medium" | "low";
  impact: string;
  recommendation: string;
};

export type StrategicIndicatorsExecutiveSummaryResponse = {
  competence: string;
  igd: number;
  igd_exact: number;
  classification: string;
  variation: ExecutiveSummaryApiVariation;
  departments: ExecutiveSummaryApiDepartment[];
  alerts_summary: ExecutiveSummaryApiAlert[];
};

export type ExecutiveDashboardDepartment = {
  id: string;
  name: string;
  shortName: string;
  weightPct: number;
  score: number;
  contribution: number;
  trend: "up" | "down" | "stable";
  strategicSummary: string;
  keyIndicators: string[];
  executiveGoal: string;
};

export type ExecutiveDashboardViewData = {
  competence: string;
  igd: number;
  igdExact: number;
  classification: string;
  variation: {
    value: number;
    direction: "up" | "down" | "stable";
    vsLabel: string;
  };
  departments: ExecutiveDashboardDepartment[];
  alertsSummary: ExecutiveSummaryApiAlert[];
};