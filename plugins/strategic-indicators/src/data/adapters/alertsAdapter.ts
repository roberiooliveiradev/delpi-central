import type {
  AlertsDashboardViewData,
  StrategicIndicatorsAlertsResponse,
} from "../types/alerts";

export function adaptAlertsToView(
  response: StrategicIndicatorsAlertsResponse,
): AlertsDashboardViewData {
  return {
    competence: response.competence,
    igdClassification: inferIgdClassification(response.executive_alerts),
    executiveAlerts: response.executive_alerts.map((item, index) => ({
      id: `executive-${index}`,
      title: item.title,
      severity: item.severity,
      impact: item.impact,
      recommendation: item.recommendation,
    })),
    departmentAlerts: response.department_alerts.map((item) => ({
      id: item.department_id,
      departmentName: item.department_name,
      currentScore: item.score,
      previousScore: item.score,
      severity: item.severity,
      reason: item.message,
      recommendation:
        "Revisar os indicadores de maior peso da área e construir plano de ação com responsáveis.",
    })),
    indicatorAlerts: response.indicator_alerts.map((item) => ({
      id: item.indicator_id,
      departmentName: item.department_name,
      indicatorName: item.indicator_name,
      simulatedScore: item.score,
      goalLabel: item.goal_label ?? "-",
      goalValue: item.goal_value ?? null,
      goalPeriodicity: item.goal_periodicity ?? null,
      goalMode: item.goal_mode ?? "standard",
      monthlyTargets: item.monthly_targets ?? [],
      performanceDirection: item.performance_direction ?? "higher_is_better",
      severity: item.severity,
      reason: item.message,
      recommendation:
        "Atuar diretamente na causa operacional do indicador e monitorar a evolução no próximo fechamento.",
    })),
    partialSuccess: Boolean(response.partial_success),
    errors: (response.errors ?? []).map((item) => ({
      departmentId: item.department_id,
      source: item.source,
      message: item.message,
    })),
  };
}

function inferIgdClassification(
  executiveAlerts: StrategicIndicatorsAlertsResponse["executive_alerts"],
): string {
  const first = executiveAlerts[0]?.title?.toLowerCase() ?? "";

  if (first.includes("crítica")) return "Crítico";
  if (first.includes("exige ação")) return "Regular, Exige Ação";
  if (first.includes("atenção")) return "Satisfatório com Alertas";
  return "Alto Desempenho";
}