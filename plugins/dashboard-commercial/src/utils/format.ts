const currencyFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const currencyCompactFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  notation: "compact",
  maximumFractionDigits: 1,
});

/** Meta ROL com target placeholder (1) gera % irreais — não exibir nesses casos. */
const MIN_MEANINGFUL_ROL_TARGET = 1_000;

export function formatPercent(
  value: number | null | undefined,
  fractionDigits = 2
): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toLocaleString("pt-BR", {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  })}%`;
}

export function formatDecimal(
  value: number | null | undefined,
  fractionDigits = 2
): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });
}

export function formatInteger(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toLocaleString("pt-BR");
}

export function formatCurrency(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return currencyFormatter.format(value);
}

export function formatCurrencyCompact(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  if (Math.abs(value) < 1_000_000) return formatCurrency(value);
  return currencyCompactFormatter.format(value);
}

export function isMeaningfulRolTarget(target: number | null | undefined): boolean {
  return target != null && !Number.isNaN(target) && target >= MIN_MEANINGFUL_ROL_TARGET;
}

export function formatRolTargetPercent(
  _rol: number | null | undefined,
  target: number | null | undefined,
  rolTargetPct: number | null | undefined
): string | null {
  if (!isMeaningfulRolTarget(target)) return null;
  if (rolTargetPct == null || Number.isNaN(rolTargetPct)) return null;
  if (rolTargetPct < 0 || rolTargetPct > 500) return null;
  return formatPercent(rolTargetPct);
}

export function buildRolKpiSubtitle(
  rol: number | null | undefined,
  target: number | null | undefined,
  rolTargetPct: number | null | undefined,
  contextLabel: string
): string {
  const parts: string[] = [];

  const pctLabel = formatRolTargetPercent(rol, target, rolTargetPct);
  if (pctLabel) {
    parts.push(`${pctLabel} da meta`);
  }

  if (isMeaningfulRolTarget(target)) {
    parts.push(`Meta ${formatCurrency(target)}`);
  }

  parts.push(contextLabel);
  return parts.join(" · ");
}

export function formatChartCurrency(value: number | string | undefined): string {
  const num = typeof value === "string" ? Number(value) : value;
  if (num == null || Number.isNaN(num)) return "—";
  return currencyFormatter.format(num);
}
