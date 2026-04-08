export type TrendDirection = "up" | "down" | "stable";

export type IgdTrendPoint = {
  period: string;
  value: number;
};

export type DepartmentTrendItem = {
  id: string;
  name: string;
  current: number;
  previous: number;
  direction: TrendDirection;
};

export type TrendFetchErrorViewItem = {
  competence: string;
  departmentId: string;
  source: string;
  message: string;
};

export type TrendsDashboardViewData = {
  competence: string;
  currentIgd: number;
  previousIgd: number;
  currentClassification: string;
  igdSeries: IgdTrendPoint[];
  departments: DepartmentTrendItem[];
  partialSuccess: boolean;
  errors: TrendFetchErrorViewItem[];
};

export type StrategicIndicatorsTrendsResponse = {
  competence: string;
  current_igd: number;
  previous_igd: number;
  current_classification: string;
  igd_series: Array<{
    period: string;
    value: number;
    classification?: string;
  }>;
  departments: Array<{
    id: string;
    name: string;
    current: number;
    previous: number;
    direction: TrendDirection;
  }>;
  errors?: Array<{
    competence: string;
    department_id: string;
    source: string;
    message: string;
  }>;
  partial_success?: boolean;
};