/** Helpers — consolidação gerencial CAPEX (Fase 2D.2). */

import { getHttpErrorCode, HttpRequestError } from "../api/httpClient";
import type {
  CapexConsolidationFilters,
  CapexConsolidationGroupItem,
} from "../types/budgetPlanning";
import { CAPEX_PLAN_STATUS_OPTIONS } from "./capexPlans";
import { BASE_PATH } from "./routing";

export const CONSOLIDATION_CURRENCY_CONFLICT =
  "budget_capex_consolidation_currency_conflict";

export const CONSOLIDATION_DETAILS_SORT_OPTIONS: { value: string; label: string }[] = [
  { value: "updated_at", label: "Atualização" },
  { value: "estimated_amount", label: "Valor previsto" },
  { value: "required_date", label: "Data Rcbto" },
  { value: "cost_center_id", label: "Centro de custo" },
  { value: "unit_id", label: "Unidade" },
  { value: "area_id", label: "Área" },
  { value: "description", label: "Descrição" },
  { value: "priority", label: "Prioridade" },
  { value: "origin", label: "Origem" },
  { value: "plan_status", label: "Status do planejamento" },
  { value: "created_at", label: "Criação" },
];

export const emptyConsolidationDraft = {
  exercise_id: "",
  unit_id: "",
  area_id: "",
  cost_center_id: "",
  category_id: "",
  priority: "",
  origin: "",
  plan_status: "",
  required_date_from: "",
  required_date_to: "",
};

export type ConsolidationDraft = typeof emptyConsolidationDraft;

export function draftToFilters(draft: ConsolidationDraft): CapexConsolidationFilters {
  return {
    exercise_id: draft.exercise_id || undefined,
    unit_id: draft.unit_id || undefined,
    area_id: draft.area_id || undefined,
    cost_center_id: draft.cost_center_id || undefined,
    category_id: draft.category_id || undefined,
    priority: draft.priority || undefined,
    origin: draft.origin || undefined,
    plan_status: draft.plan_status || undefined,
    required_date_from: draft.required_date_from || undefined,
    required_date_to: draft.required_date_to || undefined,
  };
}

export function readConsolidationDraftFromUrl(): ConsolidationDraft {
  if (typeof window === "undefined") return { ...emptyConsolidationDraft };
  const qs = new URLSearchParams(window.location.search);
  return {
    exercise_id: qs.get("exercise_id")?.trim() ?? "",
    unit_id: qs.get("unit_id")?.trim() ?? "",
    area_id: qs.get("area_id")?.trim() ?? "",
    cost_center_id: qs.get("cost_center_id")?.trim() ?? "",
    category_id: qs.get("category_id")?.trim() ?? "",
    priority: qs.get("priority")?.trim() ?? "",
    origin: qs.get("origin")?.trim() ?? "",
    plan_status: qs.get("plan_status")?.trim() ?? "",
    required_date_from: qs.get("required_date_from")?.trim() ?? "",
    required_date_to: qs.get("required_date_to")?.trim() ?? "",
  };
}

export function writeConsolidationDraftToUrl(draft: ConsolidationDraft): void {
  if (typeof window === "undefined") return;
  const qs = new URLSearchParams();
  (Object.keys(emptyConsolidationDraft) as Array<keyof ConsolidationDraft>).forEach((key) => {
    const value = draft[key]?.trim();
    if (value) qs.set(key, value);
  });
  const path = `${BASE_PATH}/capex/consolidacao`;
  const next = qs.toString() ? `${path}?${qs.toString()}` : path;
  window.history.replaceState(null, "", next);
}

export function mapCapexConsolidationError(err: unknown): string {
  const code = getHttpErrorCode(err);
  const status = err instanceof HttpRequestError ? err.status : undefined;

  if (status === 401) {
    return "Sessão expirada. Faça login novamente para continuar.";
  }
  if (status === 403 || code === "budget_capex_consolidation_forbidden") {
    return "Você não tem permissão para consultar a consolidação gerencial CAPEX.";
  }
  if (code === "budget_capex_export_forbidden") {
    return "Você não tem permissão para exportar a consolidação CAPEX.";
  }
  if (code === CONSOLIDATION_CURRENCY_CONFLICT) {
    return (
      "Há investimentos com moedas diferentes no conjunto filtrado. " +
      "Os valores não podem ser somados automaticamente. Ajuste os filtros ou normalize as moedas."
    );
  }
  if (code === "budget_capex_cost_center_forbidden") {
    return "O centro de custo selecionado está fora do seu escopo autorizado.";
  }
  if (status === 0) {
    return "Falha de rede. Verifique a conexão e tente novamente.";
  }
  if (err instanceof Error && err.message.trim()) return err.message;
  return "Não foi possível carregar a consolidação CAPEX.";
}

export function isCurrencyConflictError(err: unknown): boolean {
  return getHttpErrorCode(err) === CONSOLIDATION_CURRENCY_CONFLICT;
}

export function triggerBrowserDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.rel = "noopener";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

/** Ordena por valor decrescente e limita aos maiores (gráficos com muitos CCs). */
export function topGroupItemsByAmount(
  items: CapexConsolidationGroupItem[],
  limit: number,
): CapexConsolidationGroupItem[] {
  return [...items]
    .sort((a, b) => {
      const av = Number(a.total_amount || 0);
      const bv = Number(b.total_amount || 0);
      return bv - av;
    })
    .slice(0, limit);
}

export function consolidationPlanStatusOptions() {
  return [{ value: "", label: "Todos" }, ...CAPEX_PLAN_STATUS_OPTIONS];
}
