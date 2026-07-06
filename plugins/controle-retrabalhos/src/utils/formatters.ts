const currencyFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const integerFormatter = new Intl.NumberFormat("pt-BR");

const hoursFormatter = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const dateFormatter = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

const MONTH_ABBR_PT = [
  "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
  "Jul", "Ago", "Set", "Out", "Nov", "Dez",
] as const;

export function formatCurrencyBrl(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return currencyFormatter.format(0);
  return currencyFormatter.format(value);
}

export function formatInteger(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return integerFormatter.format(0);
  return integerFormatter.format(value);
}

export function formatHours(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return hoursFormatter.format(0);
  return `${hoursFormatter.format(value)} h`;
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

export function formatMonthLabel(item: {
  mesNome?: string;
  anoMes?: string;
  mesNumero?: number;
  ano?: number;
}): string {
  if (item.mesNumero != null && item.ano != null) {
    const monthIndex = item.mesNumero - 1;
    if (monthIndex >= 0 && monthIndex < 12) {
      return `${MONTH_ABBR_PT[monthIndex]}/${item.ano}`;
    }
  }

  const key = item.anoMes ?? "";
  const compact = /^(\d{4})(\d{2})$/.exec(key.trim());
  if (compact) {
    const monthIndex = Number(compact[2]) - 1;
    if (monthIndex >= 0 && monthIndex < 12) {
      return `${MONTH_ABBR_PT[monthIndex]}/${compact[1]}`;
    }
  }

  return key || "—";
}

export function formatPercent(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${hoursFormatter.format(value)}%`;
}

export function formatShortLabel(value: string | null | undefined, maxLength = 16): string {
  const text = (value ?? "").trim();
  if (!text) return "—";
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength - 1)}…`;
}

export function joinMotivoObservacao(motivo: string, observacao: string): string {
  const parts = [motivo.trim(), observacao.trim()].filter(Boolean);
  return parts.length ? parts.join(" — ") : "—";
}
