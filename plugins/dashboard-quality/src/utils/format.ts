const numberFormatter = new Intl.NumberFormat("pt-BR");
const decimalFormatter = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
const currencyFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  maximumFractionDigits: 0,
});

export function formatInteger(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return numberFormatter.format(value);
}

export function formatDecimal(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return decimalFormatter.format(value);
}

export function formatPpm(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${decimalFormatter.format(value)} ppm`;
}

export function formatCurrency(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return currencyFormatter.format(value);
}

export function formatScore(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return decimalFormatter.format(value);
}
