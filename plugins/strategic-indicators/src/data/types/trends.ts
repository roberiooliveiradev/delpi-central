export type TrendDirection = "up" | "down" | "stable";

export type IgdTrendPoint = {
  period: string;
  value: number;
};

export type DepartmentTrendSeriesPoint = {
  period: string;
  score: number;
  classification?: string;
  contribution?: number;
};

export type DepartmentTrendItem = {
  id: string;
  name: string;
  current: number;
  previous: number;
  direction: TrendDirection;
  lastStepDirection?: TrendDirection;
  netVariation: number;
  bestScore: number;
  worstScore: number;
  currentClassification?: string;
  currentContribution?: number;
  series: DepartmentTrendSeriesPoint[];
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
    last_step_direction?: TrendDirection;
    net_variation?: number;
    best_score?: number;
    worst_score?: number;
    current_classification?: string;
    current_contribution?: number;
    series?: Array<{
      period: string;
      score: number;
      classification?: string;
      contribution?: number;
    }>;
  }>;
  errors?: Array<{
    competence: string;
    department_id: string;
    source: string;
    message: string;
  }>;
  partial_success?: boolean;
};