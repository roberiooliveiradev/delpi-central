import type {
  DepartmentDetailsViewData,
  StrategicIndicatorsDepartmentDetailsResponse,
} from "../types/departmentDetails";

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
    strategicSummary: response.strategic_summary,
    aggregationMode: response.aggregation_mode,
    contribution: response.contribution,
    variation: {
      value: response.variation.value,
      direction: response.variation.direction,
    },
    units: response.units.map((unit) => ({
      unitId: unit.unit_id,
      unitName: unit.unit_name,
      score: unit.score,
      classification: unit.classification,
    })),
    indicators: response.indicators.map((item) => ({
      id: item.id,
      name: item.name,
      weightPct: item.weight_pct,
      goal2026: item.goal_2026,
      strategicDescription: item.strategic_description,
    })),
  };
}