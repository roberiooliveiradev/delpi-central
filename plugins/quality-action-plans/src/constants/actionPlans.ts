import type { PlanSeverity, PlanStatus } from "../types/actionPlan";

export const PAC_BRANCH_OPTIONS = [
  { value: "01", label: "Filial 01" },
  { value: "02", label: "Filial 02" },
] as const;

export const PAC_NONCONFORMITY_SCOPES = [
  { value: "external", label: "Externa" },
  { value: "internal", label: "Interna" },
] as const;

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

export type AppView =
  | "dashboard"
  | "list"
  | "overdue"
  | "recurrence"
  | "solutions"
  | "evidences"
  | "my-queue"
  | "detail"
  | "new";

export function parseRoute(pathname?: string): { view: AppView; planId?: string } {
  const path = (pathname ?? APP_BASE).replace(/\/+$/, "");

  const detailMatch = path.match(/\/plano\/([^/]+)$/);
  if (detailMatch) {
    return { view: "detail", planId: detailMatch[1] };
  }
  if (path.endsWith("/novo")) return { view: "new" };
  if (path.endsWith("/lista")) return { view: "list" };
  if (path.endsWith("/atrasados")) return { view: "overdue" };
  if (path.endsWith("/recorrencia")) return { view: "recurrence" };
  if (path.endsWith("/solucoes")) return { view: "solutions" };
  if (path.endsWith("/evidencias")) return { view: "evidences" };
  if (path.endsWith("/minha-fila")) return { view: "my-queue" };
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

export function recurrencePath(): string {
  return `${APP_BASE}/recorrencia`;
}

export function solutionsPath(): string {
  return `${APP_BASE}/solucoes`;
}

export function evidencesSearchPath(): string {
  return `${APP_BASE}/evidencias`;
}

export function myQueuePath(): string {
  return `${APP_BASE}/minha-fila`;
}

export function detailPath(planId: string): string {
  return `${APP_BASE}/plano/${planId}`;
}

export function newPlanPath(): string {
  return `${APP_BASE}/novo`;
}

export const ACTION_STATUSES: Record<string, string> = {
  pending: "Pendente",
  in_progress: "Em andamento",
  blocked: "Bloqueada",
  completed: "Concluída",
  cancelled: "Cancelada",
  overdue: "Atrasada",
};

export const EFFECTIVENESS_STATUSES: Array<{ value: string; label: string }> = [
  { value: "pending", label: "Pendente" },
  { value: "effective", label: "Eficaz" },
  { value: "partially_effective", label: "Parcialmente eficaz" },
  { value: "ineffective", label: "Ineficaz" },
  { value: "not_verified", label: "Não verificado" },
];

export function branchLabel(branchCode?: string | null): string {
  if (!branchCode) return "—";
  return PAC_BRANCH_OPTIONS.find((item) => item.value === branchCode)?.label ?? branchCode;
}

export function statusLabel(status: string): string {
  return PLAN_STATUSES.find((item) => item.value === status)?.label ?? status;
}

export function severityLabel(severity: string): string {
  return PLAN_SEVERITIES.find((item) => item.value === severity)?.label ?? severity;
}

export function nonconformityScopeLabel(scope?: string | null): string {
  return PAC_NONCONFORMITY_SCOPES.find((item) => item.value === scope)?.label ?? scope ?? "—";
}

export function actionTypeLabel(actionType: string): string {
  return ACTION_TYPES[actionType] ?? actionType;
}
