export function formatNumber(
  value: number | null | undefined,
  fractionDigits = 2,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });
}

/** Quantidades operacionais (milheiros) — ex.: 1.234,567 */
export function formatQuantity(value: number | null | undefined): string {
  return formatNumber(value, 3);
}

export function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  return value.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}
