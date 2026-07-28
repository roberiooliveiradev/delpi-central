export function formatPct(value: number | string | null | undefined, decimalPlaces?: number | null) {
  if (value === null || value === undefined || value === "") return "—";
  const num = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(num)) return String(value);
  const digits =
    typeof decimalPlaces === "number" && Number.isFinite(decimalPlaces)
      ? Math.min(6, Math.max(0, Math.trunc(decimalPlaces)))
      : 1;
  return `${num.toLocaleString("pt-BR", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}%`;
}

export function formatNumber(
  value: number | string | null | undefined,
  decimalPlaces?: number | null,
) {
  if (value === null || value === undefined || value === "") return "—";
  const num = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(num)) return String(value);
  if (typeof decimalPlaces === "number" && Number.isFinite(decimalPlaces)) {
    const digits = Math.min(6, Math.max(0, Math.trunc(decimalPlaces)));
    return num.toLocaleString("pt-BR", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
  }
  return num.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
}

/** Moeda BRL (pt-BR): R$ 1.234,56 */
export function formatCurrency(
  value: number | string | null | undefined,
  decimalPlaces?: number | null,
) {
  if (value === null || value === undefined || value === "") return "—";
  const num = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(num)) return String(value);
  if (typeof decimalPlaces === "number" && Number.isFinite(decimalPlaces)) {
    const digits = Math.min(6, Math.max(0, Math.trunc(decimalPlaces)));
    return num.toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
  }
  return num.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}
