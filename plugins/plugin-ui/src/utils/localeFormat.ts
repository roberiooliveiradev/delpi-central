import { formatDisplayValue } from "../displayFormat/formatDisplayValue";

export function formatPct(value: number | string | null | undefined, decimalPlaces?: number | null) {
  return formatDisplayValue(value, { category: "percent", decimalPlaces: decimalPlaces ?? 1 });
}

export function formatNumber(
  value: number | string | null | undefined,
  decimalPlaces?: number | null,
) {
  if (decimalPlaces == null) {
    return formatDisplayValue(value, { category: "general" });
  }
  return formatDisplayValue(value, { category: "number", decimalPlaces });
}

/** Moeda BRL (pt-BR): R$ 1.234,56 */
export function formatCurrency(
  value: number | string | null | undefined,
  decimalPlaces?: number | null,
) {
  return formatDisplayValue(value, {
    category: "currency",
    currency: "BRL",
    decimalPlaces: decimalPlaces ?? 2,
    presetId: decimalPlaces === 4 ? "currency-brl-4" : "currency-brl",
  });
}
