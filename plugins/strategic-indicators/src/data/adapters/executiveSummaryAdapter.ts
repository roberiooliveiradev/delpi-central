import type {
  ExecutiveDashboardViewData,
  StrategicIndicatorsExecutiveSummaryResponse,
} from "../types/executiveSummary";

export function adaptExecutiveSummaryToView(
  response: StrategicIndicatorsExecutiveSummaryResponse,
): ExecutiveDashboardViewData {
  return {
    competence: response.competence,
    igd: response.igd,
    igdExact: response.igd_exact,
    classification: response.classification,
    variation: {
      value: response.variation.value,
      direction: response.variation.direction,
      vsLabel: response.variation.vs_label,
    },
    departments: response.departments.map((item) => ({
      id: item.id,
      name: item.name,
      shortName: item.short_name,
      weightPct: item.weight_pct,
      score: item.score,
      contribution: item.contribution,
      trend: item.trend,
      strategicSummary: item.strategic_summary,
      keyIndicators: item.key_indicators,
      executiveGoal: item.executive_goal,
      variation: {
        value: item.variation.value,
        direction: item.variation.direction,
      },
    })),
    alertsSummary: response.alerts_summary,
  };
}