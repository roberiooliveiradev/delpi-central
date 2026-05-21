import type {
  IndicatorViewItem,
  StrategicIndicatorsResponse,
} from "../types/indicators";

function normalizeTrend(value: string): "up" | "down" | "stable" {
  if (value === "up" || value === "down" || value === "stable") {
    return value;
  }
  return "stable";
}

export function adaptIndicatorsToView(
  response: StrategicIndicatorsResponse,
): IndicatorViewItem[] {
  return response.items.map((item) => ({
    id: item.indicator_id,
    name: item.indicator_name,
    departmentId: item.department_id,
    departmentName: item.department_name,
    weightPct: item.weight_pct,
    goalLabel: item.goal_label,
    goalValue: item.goal_value,
    goalPeriodicity: item.goal_periodicity,
    goalMode: item.goal_mode,
    monthlyTargets: item.monthly_targets ?? [],
    value: item.value,
    score: item.score,
    gap: item.gap,
    hasValue: item.has_value ?? item.value !== null,
    trend: normalizeTrend(item.trend),
    classification: item.classification,
    scopeType: item.scope_type,
    performanceDirection: item.performance_direction,
    source: item.source,
    valueUnit: item.value_unit ?? null,
    valuePrefix: item.value_prefix ?? null,
    valueSuffix: item.value_suffix ?? null,
    valueDecimals: Number(item.value_decimals ?? 2),
  }));
}