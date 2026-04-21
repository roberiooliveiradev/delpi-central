import type {
  StrategicIndicatorsTrendsResponse,
  TrendsDashboardViewData,
} from "../types/trends";

function normalizeDirection(
  value: string | null | undefined,
): "up" | "down" | "stable" {
  if (value === "up" || value === "down" || value === "stable") {
    return value;
  }

  return "stable";
}

export function adaptTrendsToView(
  response: StrategicIndicatorsTrendsResponse,
): TrendsDashboardViewData {
  return {
    competence: response.competence,
    currentIgd: response.current_igd,
    previousIgd: response.previous_igd,
    currentClassification: response.current_classification,
    igdSeries: response.igd_series.map((item) => ({
      period: item.period,
      value: item.value,
      classification: item.classification,
    })),
    departments: response.departments.map((item) => ({
      id: item.id,
      name: item.name,
      current: item.current,
      previous: item.previous,
      direction: normalizeDirection(item.direction),
      lastStepDirection: normalizeDirection(
        item.last_step_direction ?? item.direction,
      ),
      netVariation: item.net_variation ?? item.current - item.previous,
      bestScore:
        item.best_score ?? Math.max(item.current, item.previous),
      worstScore:
        item.worst_score ?? Math.min(item.current, item.previous),
      currentClassification: item.current_classification,
      currentContribution: item.current_contribution,
      series: (item.series ?? [
        {
          period: "Anterior",
          score: item.previous,
        },
        {
          period: "Atual",
          score: item.current,
        },
      ]).map((point) => ({
        period: point.period,
        score: point.score,
        classification: point.classification,
        contribution: point.contribution,
      })),
    })),
    indicatorSeriesByDepartmentId: Object.fromEntries(
      Object.entries(response.indicator_series_by_department_id ?? {}).map(
        ([departmentId, indicators]) => [
          departmentId,
          (indicators ?? []).map((indicator) => ({
            indicatorId: indicator.indicator_id,
            indicatorName: indicator.indicator_name,
            weightPct: indicator.weight_pct,
            goalLabel: indicator.goal_label,
            goalValue: indicator.goal_value,
            goalPeriodicity: indicator.goal_periodicity,
            goalMode: indicator.goal_mode ?? "standard",
            monthlyTargets: (indicator.monthly_targets ?? []).map((target) => ({
              monthNumber: target.month_number,
              targetValue: target.target_value,
            })),
            scopeType: indicator.scope_type,
            performanceDirection: indicator.performance_direction,
            strategicDescription: indicator.strategic_description,
            source: indicator.source,
            series: (indicator.series ?? []).map((point) => ({
              period: point.period,
              value: point.value,
              score: point.score,
              gap: point.gap,
              classification: point.classification,
              trend: normalizeDirection(point.trend),
            })),
          })),
        ],
      ),
    ),
    partialSuccess: Boolean(response.partial_success),
    errors: (response.errors ?? []).map((item) => ({
      competence: item.competence,
      departmentId: item.department_id,
      source: item.source,
      message: item.message,
    })),
  };
}