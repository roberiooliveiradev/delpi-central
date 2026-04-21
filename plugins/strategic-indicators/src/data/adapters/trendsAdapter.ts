import type {
  StrategicIndicatorsTrendsResponse,
  TrendsDashboardViewData,
} from "../types/trends";

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
    })),
    departments: response.departments.map((department) => {
      const series =
        department.series?.length
          ? department.series.map((point) => ({
              period: point.period,
              score: point.score,
              classification: point.classification,
              contribution: point.contribution,
            }))
          : [
              {
                period: "Anterior",
                score: department.previous,
              },
              {
                period: "Atual",
                score: department.current,
              },
            ];

      return {
        id: department.id,
        name: department.name,
        current: department.current,
        previous: department.previous,
        direction: department.direction,
        lastStepDirection: department.last_step_direction ?? department.direction,
        netVariation:
          department.net_variation ?? department.current - department.previous,
        bestScore:
          department.best_score ??
          Math.max(...series.map((point) => point.score)),
        worstScore:
          department.worst_score ??
          Math.min(...series.map((point) => point.score)),
        currentClassification: department.current_classification,
        currentContribution: department.current_contribution,
        series,
      };
    }),
    partialSuccess: response.partial_success ?? false,
    errors: (response.errors ?? []).map((error) => ({
      competence: error.competence,
      departmentId: error.department_id,
      source: error.source,
      message: error.message,
    })),
  };
}