const DASH = "—";

const currency = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  maximumFractionDigits: 2,
});

const compactCurrency = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  notation: "compact",
  maximumFractionDigits: 1,
});

const integer = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });

function isNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

export function formatCurrency(value: number | null | undefined): string {
  return isNumber(value) ? currency.format(value) : DASH;
}

/** Cartões de KPI: `R$ 5,0 mi` cabe onde o valor cheio quebraria a linha. */
export function formatCompactCurrency(value: number | null | undefined): string {
  return isNumber(value) ? compactCurrency.format(value) : DASH;
}

export function formatInteger(value: number | null | undefined): string {
  return isNumber(value) ? integer.format(value) : DASH;
}

export function formatDecimal(value: number | null | undefined, decimals = 1): string {
  if (!isNumber(value)) return DASH;
  return new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

export function formatPercent(value: number | null | undefined, decimals = 1): string {
  if (!isNumber(value)) return DASH;
  return `${formatDecimal(value, decimals)}%`;
}

export function formatDays(value: number | null | undefined): string {
  if (!isNumber(value)) return DASH;
  const rounded = Math.round(value);
  return `${formatInteger(rounded)} dia${rounded === 1 ? "" : "s"}`;
}

export function formatScore(value: number | null | undefined): string {
  return isNumber(value) ? formatDecimal(value, 1) : DASH;
}

/** Formata o realizado de um indicador respeitando unidade e casas da meta. */
export function formatIndicatorValue(
  value: number | null | undefined,
  options: {
    unit?: string | null;
    prefix?: string | null;
    suffix?: string | null;
    decimals?: number | null;
  } = {},
): string {
  if (!isNumber(value)) return DASH;
  const decimals = isNumber(options.decimals) ? options.decimals : 2;
  const body = formatDecimal(value, decimals);
  const prefix = options.prefix?.trim() ?? "";
  const suffix = options.suffix?.trim() || options.unit?.trim() || "";
  const separator = suffix === "%" ? "" : " ";
  return `${prefix ? `${prefix} ` : ""}${body}${suffix ? `${separator}${suffix}` : ""}`;
}

export const EMPTY_VALUE = DASH;
