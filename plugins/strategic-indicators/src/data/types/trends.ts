export type TrendDirection = "up" | "down" | "stable";

export type IgdTrendPoint = {
  period: string;
  value: number;
  classification?: string;
};

export type DepartmentTrendSeriesPoint = {
  period: string;
  score: number;
  classification?: string;
  contribution?: number;
};

export type IndicatorTrendSeriesPoint = {
  period: string;
  value: number;
  score: number;
  gap: number;
  classification?: string;
  trend: TrendDirection;
};

export type IndicatorTrendSeriesItem = {
  indicatorId: string;
  indicatorName: string;
  weightPct: number;
  goalLabel: string;
  goalValue: number;
  goalPeriodicity: string;
  goalMode: string;
  monthlyTargets: Array<{
    monthNumber: number;
    targetValue: number;
  }>;
  scopeType: string;
  performanceDirection: string;
  strategicDescription: string;
  source: string;
  series: IndicatorTrendSeriesPoint[];
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
  indicatorSeriesByDepartmentId: Record<string, IndicatorTrendSeriesItem[]>;
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
  indicator_series_by_department_id?: Record<
    string,
    Array<{
      indicator_id: string;
      indicator_name: string;
      weight_pct: number;
      goal_label: string;
      goal_value: number;
      goal_periodicity: string;
      goal_mode?: string;
      monthly_targets?: Array<{
        month_number: number;
        target_value: number;
      }>;
      scope_type: string;
      performance_direction: string;
      strategic_description: string;
      source: string;
      series: Array<{
        period: string;
        value: number;
        score: number;
        gap: number;
        classification?: string;
        trend: TrendDirection;
      }>;
    }>
  >;
  errors?: Array<{
    competence: string;
    department_id: string;
    source: string;
    message: string;
  }>;
  partial_success?: boolean;
};