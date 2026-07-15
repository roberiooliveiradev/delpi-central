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

export function formatCurrencyBrl(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return currencyFormatter.format(0);
  return currencyFormatter.format(value);
}

export function formatInteger(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return integerFormatter.format(0);
  return integerFormatter.format(value);
}

export function formatQuantity(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return decimalFormatter.format(0);
  return decimalFormatter.format(value);
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

export function formatPercent(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${decimalFormatter.format(value)}%`;
}

export function formatSharePercent(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "0%";
  return `${value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })}%`;
}

export function formatShortLabel(value: string | null | undefined, maxLength = 18): string {
  const text = (value ?? "").trim();
  if (!text) return "—";
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength - 1)}…`;
}

/** Rótulo de ranking: código + descrição truncada (preferido nos eixos). */
export function formatRankingAxisLabel(
  code: string | null | undefined,
  label: string | null | undefined,
  maxLength = 36,
): string {
  const codeText = (code ?? "").trim();
  const desc = (label ?? "").trim();
  if (codeText && desc && desc !== codeText) {
    return formatShortLabel(`${codeText} — ${desc}`, maxLength);
  }
  return formatShortLabel(codeText || desc, maxLength);
}

export function formatMotivoLegendLabel(
  name: string,
  value: number,
  sharePct: number,
): string {
  return `${formatShortLabel(name, 32)} · ${formatCurrencyBrl(value)} (${formatSharePercent(sharePct)})`;
}
