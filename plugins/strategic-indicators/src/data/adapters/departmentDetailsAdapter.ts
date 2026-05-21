import type {
  DepartmentDetailsViewData,
  StrategicIndicatorsDepartmentDetailsResponse,
} from "../types/departmentDetails";

function normalizeTrend(value: string): "up" | "down" | "stable" {
  if (value === "up" || value === "down" || value === "stable") {
    return value;
  }
  return "stable";
}

export function adaptDepartmentDetailsToView(
  response: StrategicIndicatorsDepartmentDetailsResponse,
): DepartmentDetailsViewData {
  return {
    id: response.id,
    name: response.name,
    shortName: response.short_name,
    weightInIgd: response.weight_pct,
    score: response.score,
    classification: response.classification,
    contribution: response.contribution,
    aggregationMode: response.aggregation_mode,
    strategicSummary: response.strategic_summary,
    variation: {
      value: response.variation.value,
      direction: response.variation.direction,
    },
    units: response.units.map((unit) => ({
      unitId: unit.unit_id,
      unitName: unit.unit_name,
      score: unit.score,
      hasValue: unit.has_value,
      classification: unit.classification,
    })),
    indicators: response.indicators.map((indicator) => ({
      id: indicator.id,
      name: indicator.name,
      weightPct: indicator.weight_pct,
      goalLabel: indicator.goal_label,
      goalValue: indicator.goal_value,
      goalPeriodicity: indicator.goal_periodicity,
      goalMode: indicator.goal_mode,
      monthlyTargets: indicator.monthly_targets ?? [],
      strategicDescription: indicator.strategic_description,
      scopeType: indicator.scope_type,
      performanceDirection: indicator.performance_direction,
      realized: indicator.realized,
      hasValue: indicator.has_value,
      score: indicator.score,
      gap: indicator.gap,
      classification: indicator.classification,
      trend: normalizeTrend(indicator.trend),
      valueUnit: indicator.value_unit ?? null,
      valuePrefix: indicator.value_prefix ?? null,
      valueSuffix: indicator.value_suffix ?? null,
      valueDecimals: Number(indicator.value_decimals ?? 2),
    })),
  };
}