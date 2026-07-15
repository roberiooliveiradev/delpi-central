const currencyFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const integerFormatter = new Intl.NumberFormat("pt-BR");

const percentFormatter = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const dateFormatter = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

const MONTH_ABBR_PT = [
  "Jan",
  "Fev",
  "Mar",
  "Abr",
  "Mai",
  "Jun",
  "Jul",
  "Ago",
  "Set",
  "Out",
  "Nov",
  "Dez",
] as const;

export function formatCurrencyBrl(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return currencyFormatter.format(0);
  }
  return currencyFormatter.format(value);
}

export function formatInteger(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return integerFormatter.format(0);
  }
  return integerFormatter.format(value);
}

export function formatPercent(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${percentFormatter.format(value)}%`;
}

export function formatDatePtBr(value: string | null | undefined): string {
  if (!value) return "—";
  const parsed = parseDateInput(value);
  if (!parsed) return value;
  return dateFormatter.format(parsed);
}

export function formatMonthYearPtBr(value: string | null | undefined): string {
  if (!value) return "—";
  const isoMonth = /^(\d{4})-(\d{2})/.exec(value.trim());
  if (isoMonth) {
    const month = Number(isoMonth[2]);
    if (month >= 1 && month <= 12) {
      return `${MONTH_ABBR_PT[month - 1]}/${isoMonth[1]}`;
    }
  }
  return value;
}


export function formatPeriodRangeLabel(
  startInclusive: string | null | undefined,
  endExclusive: string | null | undefined,
): string | null {
  if (!startInclusive || !endExclusive) return null;
  const start = parseDateInput(startInclusive);
  const endExclusiveDate = parseDateInput(endExclusive);
  if (!start || !endExclusiveDate) return null;
  const endInclusive = new Date(
    endExclusiveDate.getFullYear(),
    endExclusiveDate.getMonth(),
    endExclusiveDate.getDate() - 1,
  );
  return `${dateFormatter.format(start)} a ${dateFormatter.format(endInclusive)}`;
}

export function formatTituloLabel(prefixo: string, numero: string, parcela: string): string {
  return [prefixo, numero, parcela]
    .map((part) => part.trim())
    .filter(Boolean)
    .join(" / ");
}

function parseDateInput(value: string): Date | null {
  const trimmed = value.trim();
  const iso = /^(\d{4})-(\d{2})-(\d{2})/.exec(trimmed);
  if (iso) {
    return buildLocalDate(Number(iso[1]), Number(iso[2]), Number(iso[3]));
  }
  return null;
}

function buildLocalDate(year: number, month: number, day: number): Date | null {
  const date = new Date(year, month - 1, day);
  if (
    Number.isNaN(date.getTime()) ||
    date.getFullYear() !== year ||
    date.getMonth() !== month - 1 ||
    date.getDate() !== day
  ) {
    return null;
  }
  return date;
}

export function formatUpdatedAt(date: Date): string {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}
