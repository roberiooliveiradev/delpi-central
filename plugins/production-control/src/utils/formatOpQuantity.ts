import quantityFormat from "../content/quantityFormat.json";

const DECIMAL_PLACES = Number(quantityFormat.decimalPlaces) || 3;
const EMPTY = quantityFormat.empty || "—";

/** Quantidades de OP / saldo em milheiro — sempre 3 casas (pt-BR). */
export function formatOpQuantity(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return EMPTY;
  return new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: DECIMAL_PLACES,
    maximumFractionDigits: DECIMAL_PLACES,
  }).format(value);
}
