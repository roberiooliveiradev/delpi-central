const currencyFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const integerFormatter = new Intl.NumberFormat("pt-BR");

const decimalFormatter = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 4,
});

const dateFormatter = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

/** Unidade canônica de H6_QTDPROD / H6_QTDPERDA (Protheus MI). */
export const QUANTITY_UNIT_SHORT = "mil";
export const QUANTITY_UNIT_LABEL = "milheiro";

export function quantityColumnHeader(base: string): string {
  return `${base} (${QUANTITY_UNIT_SHORT})`;
}

export function formatCurrencyBrl(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return currencyFormatter.format(0);
  return currencyFormatter.format(value);
}

export function formatInteger(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return integerFormatter.format(0);
  return integerFormatter.format(value);
}

/** Formata número na escala SH6 (milheiro), sem sufixo. */
export function formatQuantity(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return decimalFormatter.format(0);
  return decimalFormatter.format(value);
}

/** Quantidade em milheiro com unidade explícita (ex.: `3,836 mil`). */
export function formatQuantityMilheiro(value: number | null | undefined): string {
  return `${formatQuantity(value)} ${QUANTITY_UNIT_SHORT}`;
}

export function formatDatePtBr(value: string | null | undefined): string {
  if (!value) return "—";
  const iso = /^(\d{4})-(\d{2})-(\d{2})/.exec(value.trim());
  if (iso) {
    const date = new Date(Number(iso[1]), Number(iso[2]) - 1, Number(iso[3]));
    if (!Number.isNaN(date.getTime())) return dateFormatter.format(date);
  }
  return value;
}

/** Data Protheus AAAAMMDD → DD/MM/AAAA. */
export function formatProtheusDate(value: string | null | undefined): string {
  if (!value) return "—";
  const raw = value.trim();
  const match = /^(\d{4})(\d{2})(\d{2})$/.exec(raw);
  if (match) {
    const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
    if (!Number.isNaN(date.getTime())) return dateFormatter.format(date);
  }
  return formatDatePtBr(raw);
}

export function formatPercent(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${decimalFormatter.format(value)}%`;
}

export function formatShortLabel(value: string | null | undefined, maxLength = 18): string {
  const text = (value ?? "").trim();
  if (!text) return "—";
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength - 1)}…`;
}
