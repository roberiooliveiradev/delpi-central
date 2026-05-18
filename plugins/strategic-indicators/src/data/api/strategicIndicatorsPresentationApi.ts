import { STRATEGIC_INDICATORS_API_BASE } from "./strategicIndicatorsApiBase";

const BASE_URL = STRATEGIC_INDICATORS_API_BASE;

export type StrategicIndicatorsPresentationRequest = {
  competence?: string;
  branch?: string;
  startDate?: string;
  endDate?: string;
  months?: number;
  include?: string;
  getAccessToken?: () => string | undefined;
  signal?: AbortSignal;
};

type Severity = "low" | "medium" | "high";
type TrendDirection = "up" | "down" | "stable";

type IndicatorValueFormatApiFields = {
  value_unit?: string | null;
  value_prefix?: string | null;
  value_suffix?: string | null;
  value_decimals?: number | null;
};

export type StrategicIndicatorsPresentationApiResponse = {
  executive_summary: {
    competence: string;
    igd: number;
    igd_exact: number;
    classification: string;
    variation: {
      value: number;
      direction: TrendDirection;
      vs_label: string;
    };
    departments: Array<{
      id: string;
      name: string;
      short_name: string;
      weight_pct: number;
      score: number;
      contribution: number;
      trend: TrendDirection;
      strategic_summary: string;
      key_indicators: string[];
      executive_goal: string;
      variation: {
        value: number;
        direction: TrendDirection;
      };
    }>;
    alerts_summary: Array<{
      title: string;
      severity: Severity;
      impact: string;
      recommendation: string;
    }>;
    errors: Array<{
      department_id?: string | null;
      source?: string | null;
      message: string;
    }>;
    partial_success: boolean;
  };

  departments_overview: Array<{
    id: string;
    name: string;
    short_name: string;
    weight_pct: number;
    score: number;
    classification: string;
    contribution: number;
    aggregation_mode: "average_of_units" | "consolidated" | "mixed_scope";
    strategic_summary: string;
    variation: {
      value: number;
      direction: TrendDirection;
    };
  }>;

  department_details_by_id: Record<
    string,
    {
      id: string;
      name: string;
      short_name: string;
      weight_pct: number;
      score: number;
      classification: string;
      contribution: number;
      aggregation_mode: "average_of_units" | "consolidated" | "mixed_scope";
      strategic_summary: string;
      variation: {
        value: number;
        direction: TrendDirection;
      };
      units: Array<{
        unit_id: string;
        unit_name: string;
        score: number;
        classification: string;
      }>;
      indicators: Array<
        {
          id: string;
          name: string;
          weight_pct: number;
          goal_label: string;
          goal_value: number;
          goal_periodicity: string;
          goal_mode: string;
          monthly_targets: Array<{
            month_number: number;
            target_value: number;
          }>;
          strategic_description: string;
          scope_type: string;
          performance_direction: string;
          realized: Record<string, number>;
          score: number;
          gap: number;
          trend: TrendDirection;
        } & IndicatorValueFormatApiFields
      >;
      errors: Array<{
        department_id?: string | null;
        source?: string | null;
        message: string;
      }>;
      partial_success: boolean;
    }
  >;

  indicators_by_department_id: Record<
    string,
    Array<
      {
        department_id: string;
        department_name: string;
        indicator_id: string;
        indicator_name: string;
        weight_pct: number;
        goal_label: string;
        goal_value: number;
        goal_periodicity: string;
        goal_mode: string;
        monthly_targets: Array<{
          month_number: number;
          target_value: number;
        }>;
        scope_type: string;
        performance_direction: string;
        value: number;
        score: number;
        gap: number;
        trend: TrendDirection;
        classification: string;
        source: string;
      } & IndicatorValueFormatApiFields
    >
  >;

  alerts: {
    competence: string;
    executive_alerts: Array<{
      title: string;
      severity: Severity;
      impact: string;
      recommendation: string;
    }>;
    department_alerts: Array<{
      department_id: string;
      department_name: string;
      severity: Severity;
      score: number;
      previous_score?: number | null;
      variation?: number | null;
      classification: string;
      contribution: number;
      message: string;
    }>;
    indicator_alerts: Array<{
      department_id: string;
      department_name: string;
      indicator_id: string;
      indicator_name: string;
      severity: Severity;
      score: number;
      gap: number;
      classification: string;
      source: string;
      goal_label: string | null;
      goal_value: number | null;
      goal_periodicity: string | null;
      goal_mode: string;
      monthly_targets: Array<{
        month_number: number;
        target_value: number;
      }>;
      performance_direction: string;
      message: string;
    }>;
    errors: Array<{
      department_id?: string | null;
      source?: string | null;
      message: string;
    }>;
    partial_success: boolean;
  };

  trends: {
    competence: string;
    current_igd: number;
    previous_igd: number;
    current_classification: string;
    igd_series: Array<{
      period: string;
      value: number;
      classification: string;
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
      Array<
        {
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
        } & IndicatorValueFormatApiFields
      >
    >;
    errors: Array<{
      competence?: string | null;
      department_id?: string | null;
      source?: string | null;
      message: string;
    }>;
    partial_success: boolean;
  };

  meta: {
    partial_success: boolean;
    errors: Array<{
      scope?: string | null;
      competence?: string | null;
      department_id?: string | null;
      source?: string | null;
      message: string;
    }>;
  };
};

function buildQueryString(params: StrategicIndicatorsPresentationRequest) {
  const searchParams = new URLSearchParams();

  if (params.competence) searchParams.set("competence", params.competence);
  if (params.branch) searchParams.set("branch", params.branch);
  if (params.startDate) searchParams.set("start_date", params.startDate);
  if (params.endDate) searchParams.set("end_date", params.endDate);
  if (typeof params.months === "number") {
    searchParams.set("months", String(params.months));
  }
  if (params.include) {
    searchParams.set("include", params.include);
  }

  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : "";
}

function getPresentationApiUrl() {
  return `${BASE_URL}/presentation`;
}

export async function fetchStrategicIndicatorsPresentation(
  params: StrategicIndicatorsPresentationRequest,
): Promise<StrategicIndicatorsPresentationApiResponse> {
  const token = params.getAccessToken?.();

  const response = await fetch(
    `${getPresentationApiUrl()}${buildQueryString(params)}`,
    {
      method: "GET",
      signal: params.signal,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    },
  );

  if (!response.ok) {
    let detail = "Falha ao carregar presentation do Strategic Indicators.";

    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload?.detail) {
        detail = payload.detail;
      }
    } catch {
      // mantém fallback
    }

    throw new Error(detail);
  }

  return (await response.json()) as StrategicIndicatorsPresentationApiResponse;
}