/** Quantidades de OP / saldo — 3 casas decimais (pt-BR), alinhado ao Portal PCP. */
export function formatOpQuantity(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: 3,
    maximumFractionDigits: 3,
  }).format(value);
}
