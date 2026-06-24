import type { PlanSeverity, PlanStatus } from "../types/actionPlan";

export const APP_BASE = "/apps/quality-action-plans";

export const PLAN_STATUSES: Array<{ value: PlanStatus; label: string }> = [
  { value: "draft", label: "Rascunho" },
  { value: "triage", label: "Triagem" },
  { value: "containment", label: "Contenção" },
  { value: "root_cause_analysis", label: "Análise de causa" },
  { value: "action_plan_defined", label: "Plano definido" },
  { value: "in_progress", label: "Em andamento" },
  { value: "waiting_validation", label: "Aguardando validação" },
  { value: "completed", label: "Concluído" },
  { value: "cancelled", label: "Cancelado" },
];

export const PLAN_SEVERITIES: Array<{ value: PlanSeverity; label: string }> = [
  { value: "low", label: "Baixa" },
  { value: "medium", label: "Média" },
  { value: "high", label: "Alta" },
  { value: "critical", label: "Crítica" },
];

export const ACTION_TYPES: Record<string, string> = {
  containment: "Contenção",
  corrective: "Corretiva",
  preventive: "Preventiva",
  verification: "Verificação",
  standardization: "Padronização",
  training: "Treinamento",
};

export type AppView = "dashboard" | "list" | "overdue" | "detail";

export function parseRoute(pathname?: string): { view: AppView; planId?: string } {
  const path = (pathname ?? APP_BASE).replace(/\/+$/, "");

  const detailMatch = path.match(/\/plano\/([^/]+)$/);
  if (detailMatch) {
    return { view: "detail", planId: detailMatch[1] };
  }
  if (path.endsWith("/lista")) return { view: "list" };
  if (path.endsWith("/atrasados")) return { view: "overdue" };
  return { view: "dashboard" };
}

export function dashboardPath(): string {
  return APP_BASE;
}

export function listPath(): string {
  return `${APP_BASE}/lista`;
}

export function overduePath(): string {
  return `${APP_BASE}/atrasados`;
}

export function detailPath(planId: string): string {
  return `${APP_BASE}/plano/${planId}`;
}

export function statusLabel(status: string): string {
  return PLAN_STATUSES.find((item) => item.value === status)?.label ?? status;
}

export function severityLabel(severity: string): string {
  return PLAN_SEVERITIES.find((item) => item.value === severity)?.label ?? severity;
}

export function actionTypeLabel(actionType: string): string {
  return ACTION_TYPES[actionType] ?? actionType;
}
