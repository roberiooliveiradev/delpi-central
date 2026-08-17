/** Labels e formatação CAPEX — valores alinhados ao backend (spec planilha + Carta). */

import type { CapexInvestmentReviewStatus } from "../types/budgetPlanning";

export const CAPEX_PRIORITY_OPTIONS = [
  { value: "2", label: "Alta" },
  { value: "3", label: "Média" },
  { value: "4", label: "Baixa" },
] as const;

export const CAPEX_ORIGIN_OPTIONS = [
  { value: "national", label: "Nacional" },
  { value: "imported", label: "Importado" },
] as const;

export const CAPEX_CLASSIFICATION_OPTIONS = [
  { value: "1", label: "1 — Capacitação produção" },
  { value: "2", label: "2 — Reforma/Retrofiting" },
  { value: "3", label: "3 — Reposição/Substituição" },
  { value: "4", label: "4 — Segurança/Ergonomia" },
  { value: "5", label: "5 — Melhorias Q&P" },
  { value: "6", label: "6 — Outros" },
] as const;

export const CAPEX_SHIFT_OPTIONS = [
  { value: "1", label: "Turno 1" },
  { value: "2", label: "Turno 2" },
  { value: "3", label: "Turno 3" },
] as const;

export const CAPEX_STATUS_OPTIONS = [
  { value: "draft", label: "Rascunho" },
  { value: "archived", label: "Arquivado" },
] as const;

const MISSING_FIELD_LABELS: Record<string, string> = {
  description: "Descrição",
  category_id: "Categoria",
  estimated_amount: "Valor previsto",
  required_date: "Mês necessário de recebimento",
  priority: "Prioridade",
  origin: "Origem",
  cost_center_id: "Centro de custo",
  exercise_id: "Exercício",
};

export function priorityLabel(value?: string | null): string {
  if (!value) return "—";
  // Legado planilha («1 — Compra aprovada») → trata como Alta na UI.
  if (value === "1") return "Alta";
  return CAPEX_PRIORITY_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

export function originLabel(value?: string | null): string {
  if (!value) return "—";
  return CAPEX_ORIGIN_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

export function classificationLabel(value?: string | null): string {
  if (!value) return "—";
  return CAPEX_CLASSIFICATION_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

export function shiftLabel(value?: string | null): string {
  if (!value) return "—";
  return CAPEX_SHIFT_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

export function investmentStatusLabel(value?: string | null): string {
  if (!value) return "—";
  return CAPEX_STATUS_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

export function missingFieldLabel(field: string): string {
  return MISSING_FIELD_LABELS[field] ?? field;
}

/** Campos obrigatórios usados para estimar conclusão na lista (alinhado ao backend). */
const COMPLETENESS_REQUIRED_FIELDS = [
  "description",
  "category_id",
  "estimated_amount",
  "required_date",
  "priority",
  "origin",
  "cost_center_id",
] as const;

export type CapexInvestmentCompletenessSlice = {
  is_complete: boolean;
  missing_fields?: string[] | null;
  status?: string | null;
  review_status?: string | null;
};

/** Percentual 0–100 para o anel de conclusão da lista. */
export function investmentCompletenessPercent(
  row: CapexInvestmentCompletenessSlice,
): number {
  if (row.is_complete) return 100;
  const missing = new Set((row.missing_fields ?? []).map((f) => f.trim()).filter(Boolean));
  const total = COMPLETENESS_REQUIRED_FIELDS.length;
  const filled = COMPLETENESS_REQUIRED_FIELDS.filter((k) => !missing.has(k)).length;
  return Math.max(0, Math.min(100, Math.round((filled / total) * 100)));
}

export type CapexInvestmentSituationTone = "ok" | "warn" | "info" | "muted";

export type CapexInvestmentSituation = {
  key:
    | "ready"
    | "missing"
    | "drafting"
    | "archived"
    | "in_review"
    | "approved"
    | "rejected"
    | "changes_requested";
  label: string;
  tone: CapexInvestmentSituationTone;
};

export type CapexInvestmentSituationContext = {
  /** Status do plano CAPEX do centro (workflow), não do item isolado. */
  planStatus?: string | null;
};

export function investmentReviewStatus(
  row: { review_status?: string | null } | null | undefined,
): CapexInvestmentReviewStatus {
  const value = String(row?.review_status || "pending").trim();
  if (value === "approved" || value === "rejected") return value;
  return "pending";
}

export function investmentReviewLabel(status: CapexInvestmentReviewStatus): string {
  if (status === "approved") return "Aprovado";
  if (status === "rejected") return "Reprovado";
  return "Aguardando decisão";
}

export function excerptText(value?: string | null, max = 140): string {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  if (!text) return "";
  if (text.length <= max) return text;
  return `${text.slice(0, max).trimEnd()}…`;
}

/** Situação amigável para a coluna da lista (mockup cockpit). */
export function investmentSituation(
  row: CapexInvestmentCompletenessSlice,
  context?: CapexInvestmentSituationContext,
): CapexInvestmentSituation {
  if (row.status === "archived") {
    return { key: "archived", label: "Arquivado", tone: "muted" };
  }

  const review = investmentReviewStatus(row);
  if (review === "approved") {
    return { key: "approved", label: "Aprovado", tone: "ok" };
  }
  if (review === "rejected") {
    return { key: "rejected", label: "Reprovado", tone: "warn" };
  }

  const planStatus = (context?.planStatus ?? "").trim();
  if (planStatus === "submitted") {
    return { key: "in_review", label: "Aguardando decisão", tone: "info" };
  }
  if (planStatus === "approved") {
    return { key: "approved", label: "Aprovado", tone: "ok" };
  }
  if (planStatus === "rejected") {
    return { key: "rejected", label: "Reprovado", tone: "warn" };
  }

  if (planStatus === "changes_requested") {
    if (row.is_complete) {
      return { key: "changes_requested", label: "Ajustes solicitados", tone: "warn" };
    }
    const firstMissingAfterChanges = (row.missing_fields ?? []).find((f) => f.trim());
    if (firstMissingAfterChanges) {
      const field = missingFieldLabel(firstMissingAfterChanges);
      return {
        key: "missing",
        label: `Falta detalhar ${field.toLowerCase()}`,
        tone: "warn",
      };
    }
    return { key: "changes_requested", label: "Ajustes solicitados", tone: "warn" };
  }

  if (row.is_complete) {
    return { key: "ready", label: "Pronto para revisão", tone: "ok" };
  }
  const firstMissing = (row.missing_fields ?? []).find((f) => f.trim());
  if (firstMissing) {
    const field = missingFieldLabel(firstMissing);
    return {
      key: "missing",
      label: `Falta detalhar ${field.toLowerCase()}`,
      tone: "warn",
    };
  }
  return { key: "drafting", label: "Em elaboração", tone: "info" };
}

export function priorityTone(value?: string | null): "high" | "medium" | "low" | "none" {
  if (value === "2" || value === "1") return "high";
  if (value === "3") return "medium";
  if (value === "4") return "low";
  return "none";
}

/** Variante visual da barra/ícone (ciclo estável por id). */
export function investmentAccentTone(seed?: string | null): "blue" | "orange" | "teal" | "violet" {
  const s = (seed ?? "").trim();
  if (!s) return "blue";
  let hash = 0;
  for (let i = 0; i < s.length; i += 1) {
    hash = (hash * 31 + s.charCodeAt(i)) >>> 0;
  }
  const tones = ["blue", "orange", "teal", "violet"] as const;
  return tones[hash % tones.length]!;
}

/** Normaliza entrada monetária para string decimal com até 2 casas (sem float). */
export function normalizeMoneyInput(raw: string): string {
  const cleaned = raw.replace(/[^\d,.-]/g, "").trim();
  if (!cleaned || cleaned === "-" || cleaned === "," || cleaned === ".") return "";

  // Já no formato canônico da API (ponto decimal, sem milhar): "1500.50"
  if (!cleaned.includes(",") && /^-?\d+(\.\d+)?$/.test(cleaned)) {
    const neg = cleaned.startsWith("-");
    const abs = neg ? cleaned.slice(1) : cleaned;
    const [intPart = "0", fracPart = ""] = abs.split(".");
    const frac = fracPart.slice(0, 2);
    const body = frac.length ? `${intPart || "0"}.${frac}` : intPart || "0";
    return neg ? `-${body}` : body;
  }

  // Entrada BR: milhar com ponto, decimal com vírgula ("1.500,50")
  const normalized = cleaned.replace(/\./g, "").replace(",", ".");
  const neg = normalized.startsWith("-");
  const digits = (neg ? normalized.slice(1) : normalized).replace(/[^\d.]/g, "");
  const [intPart = "0", fracPart = ""] = digits.split(".");
  const frac = fracPart.slice(0, 2);
  const body = frac.length ? `${intPart || "0"}.${frac}` : intPart || "0";
  const withSign = neg ? `-${body}` : body;
  if (withSign === "-" || withSign === "-0") return "";
  return withSign;
}

/** Formata string decimal para exibição BRL (sem usar Number/float no cálculo). */
export function formatMoneyBr(value?: string | null, currency = "BRL"): string {
  if (value == null || value === "") return "—";
  const norm = normalizeMoneyInput(String(value));
  if (!norm) return "—";
  const neg = norm.startsWith("-");
  const abs = neg ? norm.slice(1) : norm;
  const [intRaw = "0", fracRaw = ""] = abs.split(".");
  const intDigits = intRaw.replace(/^0+(?=\d)/, "") || "0";
  const withThousands = intDigits.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  const frac = (fracRaw + "00").slice(0, 2);
  const formatted = `${neg ? "-" : ""}${withThousands},${frac}`;
  return currency === "BRL" ? `R$ ${formatted}` : `${formatted} ${currency}`;
}

export function isVersionConflictError(err: unknown): boolean {
  if (!err || typeof err !== "object") return false;
  const status = (err as { status?: number }).status;
  const message = String((err as { message?: string }).message ?? "");
  return status === 409 && message.includes("budget_capex_version_conflict");
}

const MONTH_NAMES_PT = [
  "Janeiro",
  "Fevereiro",
  "Março",
  "Abril",
  "Maio",
  "Junho",
  "Julho",
  "Agosto",
  "Setembro",
  "Outubro",
  "Novembro",
  "Dezembro",
] as const;

/** Opções de mês do exercício (valor = YYYY-MM). */
export function exerciseMonthOptions(
  year: number,
): ReadonlyArray<{ value: string; label: string }> {
  const y = Number.isFinite(year) && year > 1900 ? Math.trunc(year) : new Date().getFullYear();
  return MONTH_NAMES_PT.map((name, index) => {
    const month = String(index + 1).padStart(2, "0");
    return { value: `${y}-${month}`, label: `${name} de ${y}` };
  });
}

/** Converte data ISO (YYYY-MM-DD) para valor do select de mês (YYYY-MM). */
export function requiredDateToMonthValue(date?: string | null): string {
  const raw = String(date || "").trim();
  if (/^\d{4}-\d{2}/.test(raw)) return raw.slice(0, 7);
  return "";
}

/** Converte mês do select (YYYY-MM) para data canônica do plano (1º dia do mês). */
export function monthValueToRequiredDate(monthValue?: string | null): string {
  const raw = String(monthValue || "").trim();
  if (!/^\d{4}-\d{2}$/.test(raw)) return "";
  return `${raw}-01`;
}

/** Rótulo amigável do mês a partir da data ISO. */
export function requiredDateMonthLabel(date?: string | null): string {
  const ym = requiredDateToMonthValue(date);
  if (!ym) return "—";
  const [yRaw, mRaw] = ym.split("-");
  const year = Number(yRaw);
  const monthIndex = Number(mRaw) - 1;
  if (!Number.isFinite(year) || monthIndex < 0 || monthIndex > 11) return ym;
  return `${MONTH_NAMES_PT[monthIndex]} de ${year}`;
}

/** Etapas do wizard de cadastro CAPEX (modal do centro de custo). */
export const CAPEX_WIZARD_STEPS = [
  {
    id: "category",
    label: "Categoria",
    title: "Categoria do investimento",
    hint: "Escolha o tipo que melhor classifica este bem ou projeto.",
  },
  {
    id: "need",
    label: "Necessidade",
    title: "O que você precisa",
    hint: "Descreva o investimento e por que ele é necessário neste ciclo.",
  },
  {
    id: "timing",
    label: "Valor e prazo",
    title: "Quanto e quando",
    hint: "Informe valor, mês de recebimento, prioridade e origem.",
  },
  {
    id: "details",
    label: "Detalhes",
    title: "Fornecedor e detalhes",
    hint: "Campos opcionais — podem ser preenchidos depois.",
  },
  {
    id: "attachments",
    label: "Anexos",
    title: "Documentos de apoio",
    hint: "Anexar arquivos é opcional — ajuda quem for aprovar o planejamento.",
  },
] as const;

export type CapexWizardStepId = (typeof CAPEX_WIZARD_STEPS)[number]["id"];

export type CapexWizardFormSlice = {
  cost_center_id: string;
  category_id: string;
  description: string;
  estimated_amount: string;
  required_date: string;
  priority: string;
  origin: string;
};

/** Mensagem de bloqueio ao avançar a etapa (null = pode continuar). */
export function wizardStepBlockingMessage(
  stepIndex: number,
  form: CapexWizardFormSlice,
  opts?: { lockCostCenter?: boolean },
): string | null {
  const step = CAPEX_WIZARD_STEPS[stepIndex];
  if (!step) return null;
  switch (step.id) {
    case "category":
      if (!opts?.lockCostCenter && !form.cost_center_id.trim()) {
        return "Selecione o centro de custo.";
      }
      if (!form.category_id.trim()) {
        return "Selecione a categoria do investimento.";
      }
      return null;
    case "need":
      if (!form.description.trim()) {
        return "Informe a descrição do investimento.";
      }
      return null;
    case "timing":
      if (!form.estimated_amount.trim()) {
        return "Informe o valor previsto.";
      }
      if (!form.required_date.trim()) {
        return "Selecione o mês necessário de recebimento.";
      }
      if (!form.priority.trim()) {
        return "Selecione a prioridade.";
      }
      if (!form.origin.trim()) {
        return "Selecione a origem.";
      }
      return null;
    default:
      return null;
  }
}

export function isWizardStepComplete(
  stepIndex: number,
  form: CapexWizardFormSlice,
  opts?: { lockCostCenter?: boolean },
): boolean {
  return wizardStepBlockingMessage(stepIndex, form, opts) === null;
}

export function wizardProgressPercent(stepIndex: number): number {
  const total = CAPEX_WIZARD_STEPS.length;
  if (total <= 0) return 0;
  const clamped = Math.min(Math.max(stepIndex, 0), total - 1);
  return Math.round(((clamped + 1) / total) * 100);
}
