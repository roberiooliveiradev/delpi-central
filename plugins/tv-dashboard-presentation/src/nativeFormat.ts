import { formatDisplayValue } from "@delpi/plugin-ui";

/** Casas decimais permitidas na formatação de número / percentual / moeda. */
export const DECIMAL_PLACES_MIN = 0;
export const DECIMAL_PLACES_MAX = 6;

export type DecimalPlacesFormat = "number" | "percent" | "currency";

export function formatSupportsDecimalPlaces(
  format: string | null | undefined,
): format is DecimalPlacesFormat {
  return format === "number" || format === "percent" || format === "currency";
}

/** Normaliza e limita a 0–6; inválido → undefined (usa default do formato). */
export function normalizeDecimalPlaces(raw: unknown): number | undefined {
  if (typeof raw !== "number" || !Number.isFinite(raw)) return undefined;
  const n = Math.trunc(raw);
  if (n < DECIMAL_PLACES_MIN || n > DECIMAL_PLACES_MAX) {
    return Math.min(DECIMAL_PLACES_MAX, Math.max(DECIMAL_PLACES_MIN, n));
  }
  return n;
}

/**
 * Defaults de exibição quando `decimalPlaces` não está gravado.
 * (Compatível com o comportamento histórico de `nativeFormat`.)
 */
export function defaultDecimalPlacesForFormat(
  format: DecimalPlacesFormat,
): number {
  if (format === "percent") return 1;
  if (format === "currency") return 2;
  return 2;
}

export function formatPct(
  value: number | string | null | undefined,
  decimalPlaces?: number | null,
) {
  return formatDisplayValue(value, {
    category: "percent",
    decimalPlaces: decimalPlaces ?? 1,
  });
}

export function formatNumber(
  value: number | string | null | undefined,
  decimalPlaces?: number | null,
) {
  if (decimalPlaces == null) {
    return formatDisplayValue(value, { category: "number" });
  }
  return formatDisplayValue(value, { category: "number", decimalPlaces });
}

/** Moeda BRL (pt-BR): R$ 1.234,56 — arredonda conforme casas decimais. */
export function formatCurrency(
  value: number | string | null | undefined,
  decimalPlaces?: number | null,
) {
  return formatDisplayValue(value, {
    category: "currency",
    currency: "BRL",
    decimalPlaces: decimalPlaces ?? 2,
  });
}
