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
    departments: response.departments.map((item) => ({
      id: item.id,
      name: item.name,
      current: item.current,
      previous: item.previous,
      direction: item.direction,
    })),
    partialSuccess: Boolean(response.partial_success),
    errors: (response.errors ?? []).map((item) => ({
      competence: item.competence,
      departmentId: item.department_id,
      source: item.source,
      message: item.message,
    })),
  };
}