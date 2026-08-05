/** Labels e formatação CAPEX — valores alinhados ao backend (spec planilha + Carta). */

export const CAPEX_PRIORITY_OPTIONS = [
  { value: "1", label: "1 — Compra aprovada/em andamento" },
  { value: "2", label: "2 — Maior necessidade" },
  { value: "3", label: "3 — Média" },
  { value: "4", label: "4 — Menor" },
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
  required_date: "Data necessária de recebimento",
  priority: "Prioridade",
  origin: "Origem",
  cost_center_id: "Centro de custo",
  exercise_id: "Exercício",
};

export function priorityLabel(value?: string | null): string {
  if (!value) return "—";
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
