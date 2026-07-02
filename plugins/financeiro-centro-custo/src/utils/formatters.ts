const currencyFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const integerFormatter = new Intl.NumberFormat("pt-BR");

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

const dateFormatter = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

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

export function formatDatePtBr(value: string | null | undefined): string {
  if (!value) return "—";
  const parsed = parseDateInput(value);
  if (!parsed) return value;
  return dateFormatter.format(parsed);
}

export function formatMonthYearPtBr(value: string | null | undefined): string {
  if (!value) return "—";
  const parsed = parseMonthKey(value);
  if (!parsed) return value;
  const month = MONTH_ABBR_PT[parsed.getMonth()];
  return `${month}/${parsed.getFullYear()}`;
}

function parseDateInput(value: string): Date | null {
  const trimmed = value.trim();

  const iso = /^(\d{4})-(\d{2})-(\d{2})/.exec(trimmed);
  if (iso) {
    return buildLocalDate(Number(iso[1]), Number(iso[2]), Number(iso[3]));
  }

  const protheus = /^(\d{4})(\d{2})(\d{2})$/.exec(trimmed);
  if (protheus) {
    return buildLocalDate(Number(protheus[1]), Number(protheus[2]), Number(protheus[3]));
  }

  const brazilian = /^(\d{2})\/(\d{2})\/(\d{4})/.exec(trimmed);
  if (brazilian) {
    return buildLocalDate(Number(brazilian[3]), Number(brazilian[2]), Number(brazilian[1]));
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

function parseMonthKey(value: string): Date | null {
  const trimmed = value.trim();

  const iso = /^(\d{4})-(\d{2})$/.exec(trimmed);
  if (iso) {
    return buildLocalDate(Number(iso[1]), Number(iso[2]), 1);
  }

  const compact = /^(\d{4})(\d{2})$/.exec(trimmed);
  if (compact) {
    return buildLocalDate(Number(compact[1]), Number(compact[2]), 1);
  }

  return null;
}

export function formatSupplierLabel(
  codigo: string,
  loja: string,
  razaoSocial: string,
): string {
  const code = [codigo, loja].filter(Boolean).join("/");
  return razaoSocial ? `${razaoSocial} (${code})` : code;
}

export function formatCostCenterLabel(codigo: string, descricao: string): string {
  if (!codigo && !descricao) return "—";
  if (!descricao) return codigo;
  if (!codigo) return descricao;
  return `${codigo} — ${descricao}`;
}

export function formatPercent(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value)}%`;
}
