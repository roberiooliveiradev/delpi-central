export type DepartmentVariationApi = {
  value: number;
  direction: "up" | "down" | "stable";
};

export type StrategicIndicatorsDepartmentListItemApi = {
  id: string;
  name: string;
  short_name: string;
  weight_pct: number;
  score: number;
  classification: string;
  contribution: number;
  aggregation_mode: "average_of_units" | "consolidated" | "mixed_scope";
  strategic_summary: string;
  variation: DepartmentVariationApi;
};

export type StrategicIndicatorsDepartmentsResponse = {
  items: StrategicIndicatorsDepartmentListItemApi[];
};

export type DepartmentOverviewViewItem = {
  id: string;
  name: string;
  shortName: string;
  weightInIgd: number;
  score: number;
  classification: string;
  strategicSummary: string;
};