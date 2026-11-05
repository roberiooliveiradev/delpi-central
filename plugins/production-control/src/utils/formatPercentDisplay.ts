/**
 * Formata percentual para exibição PCP (pt-BR), no máximo 2 casas decimais.
 * Ex.: "-28.65432" → "-28,65%" · "100" → "100%"
 */
export function formatPercentDisplay(
  value: string | number | null | undefined,
  empty = "—",
): string {
  if (value == null) return empty;
  const raw = typeof value === "number" ? String(value) : value.trim();
  if (!raw) return empty;
  const numeric = Number(raw.replace(",", "."));
  if (!Number.isFinite(numeric)) return empty;
  const formatted = numeric.toLocaleString("pt-BR", {
    maximumFractionDigits: 2,
    minimumFractionDigits: 0,
  });
  return `${formatted}%`;
}
