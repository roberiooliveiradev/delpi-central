import { PLAN_SEVERITIES, PLAN_STATUSES, statusLabel, severityLabel } from "../constants/actionPlans";
import { CHART_COLORS } from "../constants/chartColors";
import type { ActionPlanSummary, DashboardSummary } from "../types/actionPlan";

export function buildOverviewChartData(summary: DashboardSummary) {
  return [
    { name: "Abertos", value: summary.open_plans, fill: CHART_COLORS[0] },
    { name: "Críticos", value: summary.critical_open, fill: CHART_COLORS[5] },
    { name: "Com atraso", value: summary.overdue_plans, fill: CHART_COLORS[4] },
    { name: "Ações atrasadas", value: summary.overdue_actions, fill: CHART_COLORS[3] },
    { name: "Validação", value: summary.waiting_validation, fill: CHART_COLORS[1] },
    { name: "Concluídos/mês", value: summary.completed_this_month, fill: "var(--success, #067647)" },
  ];
}

export function buildBranchChartData(summary: DashboardSummary) {
  return (summary.by_branch ?? []).map((branch, index) => ({
    branch: `Filial ${branch.branch_code}`,
    abertos: branch.open_plans,
    criticos: branch.critical_open,
    fill: CHART_COLORS[index % CHART_COLORS.length],
  }));
}

export function buildStatusDistribution(items: ActionPlanSummary[]) {
  const counts = new Map<string, number>();
  for (const plan of items) {
    counts.set(plan.status, (counts.get(plan.status) ?? 0) + 1);
  }

  return PLAN_STATUSES.map((status, index) => ({
    name: status.label,
    value: counts.get(status.value) ?? 0,
    fill: CHART_COLORS[index % CHART_COLORS.length],
  })).filter((entry) => entry.value > 0);
}

export function buildSeverityDistribution(items: ActionPlanSummary[]) {
  const counts = new Map<string, number>();
  for (const plan of items) {
    counts.set(plan.severity, (counts.get(plan.severity) ?? 0) + 1);
  }

  return PLAN_SEVERITIES.map((severity, index) => ({
    name: severity.label,
    value: counts.get(severity.value) ?? 0,
    fill: CHART_COLORS[index % CHART_COLORS.length],
  })).filter((entry) => entry.value > 0);
}

export function statusDistributionLabel(status: string): string {
  return statusLabel(status);
}

export function severityDistributionLabel(severity: string): string {
  return severityLabel(severity);
}
