export type StrategicIndicatorsPresentationRequest = {
  competence?: string;
  branch?: string;
  startDate?: string;
  endDate?: string;
  months?: number;
  getAccessToken?: () => string | undefined;
  signal?: AbortSignal;
};

const BASE_URL = "/apps/api-delpi/strategic-indicators";

type Severity = "low" | "medium" | "high";
type TrendDirection = "up" | "down" | "stable";

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
    aggregation_mode: string;
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
      aggregation_mode: string;
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
      indicators: Array<{
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
      }>;
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
    Array<{
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
    }>
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
    }>;
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

function buildHeaders(
  getAccessToken?: () => string | undefined,
): HeadersInit {
  const token = getAccessToken?.();

  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function buildQuery(params: {
  competence?: string;
  branch?: string;
  startDate?: string;
  endDate?: string;
  months?: number;
}) {
  const query = new URLSearchParams();

  if (params.competence) query.set("competence", params.competence);
  if (params.branch) query.set("branch", params.branch);
  if (params.startDate) query.set("start_date", params.startDate);
  if (params.endDate) query.set("end_date", params.endDate);
  if (typeof params.months === "number") {
    query.set("months", String(params.months));
  }

  const asString = query.toString();
  return asString ? `?${asString}` : "";
}

export async function fetchStrategicIndicatorsPresentation({
  competence,
  branch,
  startDate,
  endDate,
  months,
  getAccessToken,
  signal,
}: StrategicIndicatorsPresentationRequest): Promise<StrategicIndicatorsPresentationApiResponse> {
  const response = await fetch(
    `${BASE_URL}/presentation${buildQuery({
      competence,
      branch,
      startDate,
      endDate,
      months,
    })}`,
    {
      method: "GET",
      headers: buildHeaders(getAccessToken),
      signal,
    },
  );

  if (!response.ok) {
    const message = await safeReadError(response);
    throw new Error(
      message || "Falha ao carregar presentation do Strategic Indicators.",
    );
  }

  return response.json();
}

async function safeReadError(response: Response): Promise<string | null> {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string") return data.detail;
    if (typeof data?.message === "string") return data.message;
    return null;
  } catch {
    return null;
  }
}