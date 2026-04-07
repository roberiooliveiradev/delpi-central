import type {
  IndicatorViewItem,
  StrategicIndicatorsResponse,
} from "../types/indicators";

export function adaptIndicatorsToView(
  response: StrategicIndicatorsResponse,
): IndicatorViewItem[] {
  return response.items.map((item) => ({
    id: item.indicator_id,
    departmentId: item.department_id,
    departmentName: item.department_name,
    name: item.indicator_name,
    weightPct: item.weight_pct,
    goal2026: item.goal_2026,
    value: item.value,
    score: item.score,
    gap: item.gap,
    trend: item.trend,
    classification: item.classification,
    source: item.source,
  }));
}