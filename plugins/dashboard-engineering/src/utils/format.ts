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

/** Percentual já em escala 0–100 (ex.: 85,5 = 85,5%). */
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

/** ROI da transformometro-api: razão (ex.: 3,36 = 336% de retorno sobre investimento). */
export function formatRoiRatio(
  value: number | null | undefined,
  fractionDigits = 1
): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${(value * 100).toLocaleString("pt-BR", {
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

export function formatChartCurrency(value: number | string | undefined): string {
  const num = typeof value === "string" ? Number(value) : value;
  if (num == null || Number.isNaN(num)) return "—";
  return currencyFormatter.format(num);
}
