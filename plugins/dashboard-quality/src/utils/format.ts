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

export function formatNonconformityCode(
  code: string | null | undefined,
  codeDisplay?: string | null
): string {
  const display = codeDisplay?.trim();
  if (display) return display;
  if (!code?.trim()) return "—";

  const raw = code.trim();
  if (raw.length < 5) return raw;

  const year = raw.slice(-4);
  if (!/^\d{4}$/.test(year)) return raw;

  const sequence = raw.slice(0, -4).replace(/^0+/, "") || "0";
  if (!/^\d+$/.test(sequence)) return raw;

  return `${Number(sequence)}/${year}`;
}

export function formatCustomerRef(
  code: string | null | undefined,
  store: string | null | undefined
): string {
  const customerCode = code?.trim();
  if (!customerCode) return "—";

  const customerStore = store?.trim();
  return customerStore ? `${customerCode}/${customerStore}` : customerCode;
}
