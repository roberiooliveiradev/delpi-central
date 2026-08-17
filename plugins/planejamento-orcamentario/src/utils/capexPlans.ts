/** Labels e helpers do planejamento CAPEX por centro de custo (Fase 2C.2). */

import { getHttpErrorCode, HttpRequestError } from "../api/httpClient";
import type {
  CapexInvestment,
  CapexPlan,
  CapexPlanHistoryAction,
  CapexPlanIncompleteInvestment,
  CapexPlanStatus,
} from "../types/budgetPlanning";
import { normalizeMoneyInput } from "./capexInvestments";

export const CAPEX_PLAN_STATUS_OPTIONS: { value: CapexPlanStatus; label: string }[] = [
  { value: "draft", label: "Rascunho" },
  { value: "submitted", label: "Enviado para aprovação" },
  { value: "changes_requested", label: "Ajustes solicitados" },
  { value: "rejected", label: "Reprovado" },
  { value: "approved", label: "Aprovado" },
];

const HISTORY_ACTION_LABELS: Record<CapexPlanHistoryAction, string> = {
  created: "Planejamento criado",
  submitted: "Enviado para aprovação",
  request_changes: "Ajustes solicitados",
  rejected: "Reprovado",
  approved: "Aprovado",
  investment_approved: "Investimento aprovado",
  investment_rejected: "Investimento reprovado",
};

const EDITABLE_STATUSES = new Set<string>(["draft", "changes_requested"]);
const LOCKED_STATUSES = new Set<string>(["submitted", "rejected", "approved"]);

export function planStatusLabel(status?: string | null): string {
  if (!status) return "—";
  return CAPEX_PLAN_STATUS_OPTIONS.find((o) => o.value === status)?.label ?? status;
}

export function planHistoryActionLabel(action?: string | null): string {
  if (!action) return "—";
  return HISTORY_ACTION_LABELS[action as CapexPlanHistoryAction] ?? action;
}

/** Nome completo de quem enviou o plano — nunca exibir o sub/UUID cru. */
export function planSubmitterDisplayName(
  plan: {
    submitted_by_name?: string | null;
    submitted_by?: string | null;
  } | null | undefined,
  history?: Array<{ action?: string | null; actor_name?: string | null }> | null,
): string {
  const fromPlan = String(plan?.submitted_by_name || "").trim();
  if (fromPlan) return fromPlan;
  const fromHistory = (history ?? [])
    .filter((h) => h.action === "submitted")
    .map((h) => String(h.actor_name || "").trim())
    .find(Boolean);
  if (fromHistory) return fromHistory;
  return "—";
}

/** Plano inexistente ≡ draft (editável). */
export function isPlanEditable(plan: CapexPlan | null | undefined): boolean {
  if (!plan) return true;
  return EDITABLE_STATUSES.has(String(plan.status));
}

export function isPlanLocked(plan: CapexPlan | null | undefined): boolean {
  if (!plan) return false;
  return LOCKED_STATUSES.has(String(plan.status));
}

export function canSubmitPlanStatus(plan: CapexPlan | null | undefined): boolean {
  if (!plan) return false;
  return EDITABLE_STATUSES.has(String(plan.status));
}

export function planLockReason(plan: CapexPlan | null | undefined): string | null {
  if (!plan) return null;
  switch (plan.status) {
    case "submitted":
      return "O planejamento foi enviado e está em análise. Edição, arquivamento e anexos ficam bloqueados até a decisão.";
    case "rejected":
      return "Este planejamento foi reprovado e permanece somente leitura.";
    case "approved":
      return "Este planejamento foi aprovado e não pode mais ser alterado.";
    default:
      return null;
  }
}

export function activeInvestments(items: CapexInvestment[]): CapexInvestment[] {
  return items.filter((i) => String(i.status) === "draft");
}

export function incompleteInvestments(items: CapexInvestment[]): CapexInvestment[] {
  return activeInvestments(items).filter((i) => !i.is_complete);
}

/** Soma valores estimados como string decimal (sem float). */
export function sumEstimatedAmounts(
  items: { estimated_amount?: string | null }[],
): string {
  let cents = 0n;
  for (const item of items) {
    const norm = normalizeMoneyInput(String(item.estimated_amount ?? ""));
    if (!norm) continue;
    const neg = norm.startsWith("-");
    const abs = neg ? norm.slice(1) : norm;
    const [intRaw = "0", fracRaw = ""] = abs.split(".");
    const frac = (fracRaw + "00").slice(0, 2);
    const value = BigInt(intRaw || "0") * 100n + BigInt(frac || "0");
    cents += neg ? -value : value;
  }
  const neg = cents < 0n;
  const abs = neg ? -cents : cents;
  const intPart = abs / 100n;
  const fracPart = abs % 100n;
  return `${neg ? "-" : ""}${intPart}.${fracPart.toString().padStart(2, "0")}`;
}

export function formatDateTimeBr(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-BR");
}

export function isPlanVersionConflictError(err: unknown): boolean {
  const code = getHttpErrorCode(err);
  if (code === "budget_capex_plan_version_conflict") return true;
  if (!(err instanceof HttpRequestError) || err.status !== 409) return false;
  return String(err.message).includes("budget_capex_plan_version_conflict");
}

export function isPlanIncompleteError(err: unknown): boolean {
  return getHttpErrorCode(err) === "budget_capex_plan_incomplete";
}

export function extractIncompleteInvestments(
  err: unknown,
): CapexPlanIncompleteInvestment[] {
  if (!(err instanceof HttpRequestError) || !err.meta) return [];
  const raw = err.meta.incomplete_investments;
  if (!Array.isArray(raw)) return [];
  return raw.filter((row): row is CapexPlanIncompleteInvestment => !!row && typeof row === "object");
}

export function mapCapexPlanError(err: unknown): string {
  const code = getHttpErrorCode(err);
  switch (code) {
    case "budget_capex_plan_incomplete":
      return "Há investimentos incompletos. Corrija os campos pendentes antes de enviar.";
    case "budget_capex_plan_version_conflict":
      return "O planejamento foi alterado em outra sessão. Recarregue os dados e tente novamente.";
    case "budget_capex_plan_comment_required":
      return "Comentário ou justificativa é obrigatório para esta decisão.";
    case "budget_capex_plan_already_approved":
      return "Este planejamento já foi aprovado e não aceita nova decisão.";
    case "budget_capex_plan_locked":
      return "O planejamento está bloqueado para edição no status atual.";
    case "budget_capex_plan_invalid_transition":
      return "Esta ação não é permitida no status atual do planejamento.";
    case "budget_capex_plan_not_found":
      return "Planejamento CAPEX não encontrado ou sem permissão de visualização.";
    case "budget_capex_investment_not_found":
      return "Investimento não encontrado neste planejamento.";
    case "budget_capex_investment_review_invalid":
      return "Não foi possível registrar a decisão deste investimento.";
    case "budget_capex_approval_forbidden":
      return "Sem permissão para esta operação de submissão ou aprovação.";
    default:
      break;
  }
  if (err instanceof HttpRequestError && err.status === 401) {
    return "Sessão expirada (401). Faça login novamente.";
  }
  if (err instanceof HttpRequestError && err.status === 403) {
    return "Acesso negado (403) a esta operação CAPEX.";
  }
  return err instanceof Error ? err.message : "Erro inesperado no planejamento CAPEX.";
}
