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

function resolveFractionDigits(
  format: DecimalPlacesFormat,
  decimalPlaces?: number | null,
): { min: number; max: number } {
  const explicit = normalizeDecimalPlaces(decimalPlaces ?? undefined);
  if (explicit != null) {
    return { min: explicit, max: explicit };
  }
  if (format === "percent") return { min: 1, max: 1 };
  if (format === "currency") return { min: 2, max: 2 };
  // number histórico: até 2 casas, sem forçar zeros à direita
  return { min: 0, max: 2 };
}

export function formatPct(
  value: number | string | null | undefined,
  decimalPlaces?: number | null,
) {
  if (value === null || value === undefined || value === "") return "—";
  const num = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(num)) return String(value);
  const { min, max } = resolveFractionDigits("percent", decimalPlaces);
  return `${num.toLocaleString("pt-BR", {
    minimumFractionDigits: min,
    maximumFractionDigits: max,
  })}%`;
}

export function formatNumber(
  value: number | string | null | undefined,
  decimalPlaces?: number | null,
) {
  if (value === null || value === undefined || value === "") return "—";
  const num = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(num)) return String(value);
  const { min, max } = resolveFractionDigits("number", decimalPlaces);
  return num.toLocaleString("pt-BR", {
    minimumFractionDigits: min,
    maximumFractionDigits: max,
  });
}

/** Moeda BRL (pt-BR): R$ 1.234,56 — arredonda conforme casas decimais. */
export function formatCurrency(
  value: number | string | null | undefined,
  decimalPlaces?: number | null,
) {
  if (value === null || value === undefined || value === "") return "—";
  const num = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(num)) return String(value);
  const { min, max } = resolveFractionDigits("currency", decimalPlaces);
  return num.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: min,
    maximumFractionDigits: max,
  });
}
