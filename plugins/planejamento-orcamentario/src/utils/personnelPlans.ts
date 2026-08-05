/** Utilitários — Orçamento de Pessoal (Fase 3B.2 / 3C.2). */

import { getHttpErrorCode, HttpRequestError } from "../api/httpClient";
import type {
  PersonnelHeadcountField,
  PersonnelPlan,
  PersonnelPlanHistoryAction,
  PersonnelPlanIncompleteLine,
  PersonnelPlanLine,
  PersonnelPlanLineCreateInput,
  PersonnelPlanLineUpdateInput,
  PersonnelPlanStatus,
} from "../types/budgetPlanning";

export const POSITION_NAME_MAX_LENGTH = 200;
export const PERSONNEL_AUTOSAVE_MS = 1000;

export const HEADCOUNT_COLUMNS: {
  field: PersonnelHeadcountField;
  label: string;
}[] = [
  { field: "headcount_dec_2025", label: "Dez/2025" },
  { field: "headcount_oct_2026", label: "Out/2026" },
  { field: "headcount_forecast", label: "Previsto" },
  { field: "headcount_dec_2027", label: "Dez/2027" },
];

export type PersonnelSaveStatus = "idle" | "dirty" | "saving" | "saved" | "error";

export function personnelSaveStatusLabel(status: PersonnelSaveStatus): string {
  switch (status) {
    case "dirty":
      return "Alterado";
    case "saving":
      return "Salvando";
    case "saved":
      return "Salvo";
    case "error":
      return "Erro";
    default:
      return "";
  }
}

export function normalizePositionName(value: string | null | undefined): string {
  return String(value ?? "").trim();
}

export function positionNameKey(value: string | null | undefined): string {
  return normalizePositionName(value).toLocaleLowerCase("pt-BR");
}

export function validatePositionName(
  value: string | null | undefined,
): { ok: true; name: string } | { ok: false; code: string; message: string } {
  const name = normalizePositionName(value);
  if (!name) {
    return {
      ok: false,
      code: "budget_personnel_position_name_required",
      message: "Informe o nome do cargo.",
    };
  }
  if (name.length > POSITION_NAME_MAX_LENGTH) {
    return {
      ok: false,
      code: "budget_personnel_position_name_too_long",
      message: `Nome do cargo deve ter no máximo ${POSITION_NAME_MAX_LENGTH} caracteres.`,
    };
  }
  return { ok: true, name };
}

/** Parse headcount digitado: vazio → null; rejeita negativo e não-inteiro. */
export function parseHeadcountInput(
  raw: string,
): { ok: true; value: number | null } | { ok: false; message: string } {
  const trimmed = String(raw ?? "").trim();
  if (!trimmed) return { ok: true, value: null };
  if (!/^\d+$/.test(trimmed)) {
    return {
      ok: false,
      message: "Headcount deve ser um inteiro ≥ 0.",
    };
  }
  const value = Number(trimmed);
  if (!Number.isSafeInteger(value) || value < 0) {
    return {
      ok: false,
      message: "Headcount não pode ser negativo.",
    };
  }
  return { ok: true, value };
}

export function headcountToInput(value: number | null | undefined): string {
  if (value === null || value === undefined) return "";
  return String(value);
}

export const PERSONNEL_PLAN_STATUS_OPTIONS: {
  value: PersonnelPlanStatus;
  label: string;
}[] = [
  { value: "draft", label: "Rascunho" },
  { value: "submitted", label: "Enviado para aprovação" },
  { value: "changes_requested", label: "Ajustes solicitados" },
  { value: "rejected", label: "Reprovado" },
  { value: "approved", label: "Aprovado" },
];

const HISTORY_ACTION_LABELS: Record<PersonnelPlanHistoryAction, string> = {
  created: "Planejamento criado",
  submitted: "Enviado para aprovação",
  request_changes: "Ajustes solicitados",
  rejected: "Reprovado",
  approved: "Aprovado",
};

const EDITABLE_PLAN_STATUSES = new Set<string>(["draft", "changes_requested"]);
const LOCKED_PLAN_STATUSES = new Set<string>(["submitted", "rejected", "approved"]);

export function personnelPlanStatusLabel(status?: string | null): string {
  if (!status) return "—";
  return (
    PERSONNEL_PLAN_STATUS_OPTIONS.find((o) => o.value === status)?.label ?? status
  );
}

export function personnelPlanHistoryActionLabel(action?: string | null): string {
  if (!action) return "—";
  return HISTORY_ACTION_LABELS[action as PersonnelPlanHistoryAction] ?? action;
}

export function isPersonnelPlanEditable(
  plan: PersonnelPlan | null | undefined,
): boolean {
  if (!plan) return true;
  return EDITABLE_PLAN_STATUSES.has(String(plan.status));
}

export function isPersonnelPlanLocked(
  plan: PersonnelPlan | null | undefined,
): boolean {
  if (!plan) return false;
  return LOCKED_PLAN_STATUSES.has(String(plan.status));
}

export function canSubmitPersonnelPlanStatus(
  plan: PersonnelPlan | null | undefined,
): boolean {
  if (!plan) return false;
  return EDITABLE_PLAN_STATUSES.has(String(plan.status));
}

export function personnelPlanLockReason(
  plan: PersonnelPlan | null | undefined,
): string | null {
  if (!plan) return null;
  switch (plan.status) {
    case "submitted":
      return "O orçamento foi enviado e está em análise. A edição das linhas fica bloqueada até a decisão.";
    case "rejected":
      return "Este orçamento foi reprovado e permanece somente leitura.";
    case "approved":
      return "Este orçamento foi aprovado e não pode mais ser alterado.";
    default:
      return null;
  }
}

export function formatPersonnelDateTimeBr(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-BR");
}

export function headcountFieldLabel(field: string): string {
  return HEADCOUNT_COLUMNS.find((c) => c.field === field)?.label ?? field;
}

export function isPersonnelVersionConflictError(err: unknown): boolean {
  if (!(err instanceof HttpRequestError) && (!err || typeof err !== "object")) {
    return false;
  }
  const status = (err as { status?: number }).status;
  const code = getHttpErrorCode(err);
  const message = String((err as { message?: string }).message ?? "");
  return (
    status === 409 &&
    (code === "budget_personnel_line_version_conflict" ||
      message.includes("budget_personnel_line_version_conflict"))
  );
}

export function isPersonnelPlanVersionConflictError(err: unknown): boolean {
  const code = getHttpErrorCode(err);
  if (code === "budget_personnel_plan_version_conflict") return true;
  if (!(err instanceof HttpRequestError) || err.status !== 409) return false;
  return String(err.message).includes("budget_personnel_plan_version_conflict");
}

export function isPersonnelPlanIncompleteError(err: unknown): boolean {
  return getHttpErrorCode(err) === "budget_personnel_plan_incomplete";
}

export function isPersonnelPlanLockedError(err: unknown): boolean {
  return getHttpErrorCode(err) === "budget_personnel_plan_locked";
}

export function extractIncompletePersonnelLines(
  err: unknown,
): PersonnelPlanIncompleteLine[] {
  if (!(err instanceof HttpRequestError) || !err.meta) return [];
  const raw = err.meta.incomplete_lines;
  if (!Array.isArray(raw)) return [];
  return raw.filter(
    (row): row is PersonnelPlanIncompleteLine => !!row && typeof row === "object",
  );
}

export function mapPersonnelError(err: unknown): string {
  const code = getHttpErrorCode(err);
  switch (code) {
    case "budget_personnel_plan_incomplete":
      return "Há linhas incompletas. Corrija os campos pendentes antes de enviar.";
    case "budget_personnel_plan_version_conflict":
      return "O planejamento foi alterado em outra sessão. Recarregue os dados e tente novamente.";
    case "budget_personnel_plan_comment_required":
      return "Comentário ou justificativa é obrigatório para esta decisão.";
    case "budget_personnel_plan_already_approved":
      return "Este orçamento já foi aprovado e não aceita nova decisão.";
    case "budget_personnel_plan_locked":
      return "O orçamento está bloqueado para edição no status atual. Recarregue para ver o status atualizado.";
    case "budget_personnel_plan_invalid_transition":
      return "Esta ação não é permitida no status atual do orçamento.";
    case "budget_personnel_plan_not_found":
      return "Orçamento de Pessoal não encontrado ou sem permissão de visualização.";
    case "budget_personnel_approval_forbidden":
      return "Quem submeteu o plano não pode decidir sobre o próprio orçamento (segregação de funções).";
    case "budget_personnel_responsibility_required":
      return "Sem responsabilidade de Pessoal para este centro de custo.";
    default:
      break;
  }
  if (err instanceof HttpRequestError) {
    if (err.status === 401) return "Sessão expirada (401). Faça login novamente.";
    if (err.status === 403) {
      return "Acesso negado (403) ao Orçamento de Pessoal.";
    }
  }
  const message =
    err instanceof Error ? err.message : "Erro no Orçamento de Pessoal.";
  if (code && !message.includes(`[${code}]`)) {
    return `[${code}] ${message}`;
  }
  return message;
}

export function buildPersonnelLineCreatePayload(input: {
  position_name: string;
  headcount_dec_2025: string;
  headcount_oct_2026: string;
  headcount_forecast: string;
  headcount_dec_2027: string;
  observations: string;
}):
  | { ok: true; payload: PersonnelPlanLineCreateInput }
  | { ok: false; message: string; code?: string } {
  const nameCheck = validatePositionName(input.position_name);
  if (!nameCheck.ok) {
    return { ok: false, message: nameCheck.message, code: nameCheck.code };
  }
  const payload: PersonnelPlanLineCreateInput = {
    position_name: nameCheck.name,
    observations: input.observations.trim() || null,
  };
  for (const { field } of HEADCOUNT_COLUMNS) {
    const parsed = parseHeadcountInput(input[field]);
    if (!parsed.ok) {
      return {
        ok: false,
        message: parsed.message,
        code: "budget_personnel_invalid_headcount",
      };
    }
    payload[field] = parsed.value;
  }
  return { ok: true, payload };
}

export function buildPersonnelLineUpdatePayload(
  version: number,
  input: {
    position_name: string;
    headcount_dec_2025: string;
    headcount_oct_2026: string;
    headcount_forecast: string;
    headcount_dec_2027: string;
    observations: string;
  },
):
  | { ok: true; payload: PersonnelPlanLineUpdateInput }
  | { ok: false; message: string; code?: string } {
  const created = buildPersonnelLineCreatePayload(input);
  if (!created.ok) return created;
  return {
    ok: true,
    payload: {
      version,
      ...created.payload,
    },
  };
}

export function lineFromServer(row: PersonnelPlanLine): {
  id: string;
  position_name: string;
  headcount_dec_2025: string;
  headcount_oct_2026: string;
  headcount_forecast: string;
  headcount_dec_2027: string;
  observations: string;
  version: number;
} {
  return {
    id: row.id,
    position_name: row.position_name ?? "",
    headcount_dec_2025: headcountToInput(row.headcount_dec_2025),
    headcount_oct_2026: headcountToInput(row.headcount_oct_2026),
    headcount_forecast: headcountToInput(row.headcount_forecast),
    headcount_dec_2027: headcountToInput(row.headcount_dec_2027),
    observations: row.observations ?? "",
    version: row.version,
  };
}

export function findDuplicatePositionName(
  lines: Array<{ localKey: string; position_name: string; is_active?: boolean }>,
  candidate: string,
  excludeLocalKey?: string,
): boolean {
  const key = positionNameKey(candidate);
  if (!key) return false;
  return lines.some((ln) => {
    if (excludeLocalKey && ln.localKey === excludeLocalKey) return false;
    if (ln.is_active === false) return false;
    return positionNameKey(ln.position_name) === key;
  });
}
