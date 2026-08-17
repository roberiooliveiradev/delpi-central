export const QUANTITY_DECIMALS = 3;

export function formatMoney(value: number | null | undefined): string {
  if (value == null || Number.isNaN(Number(value))) return "—";
  return Number(value).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

export function formatQuantity(value: number | null | undefined): string {
  if (value == null || Number.isNaN(Number(value))) return "—";
  const rounded = roundQuantity(Number(value));
  const sign = rounded < 0 ? "-" : "";
  const [intPart, frac = ""] = Math.abs(rounded).toFixed(QUANTITY_DECIMALS).split(".");
  const grouped = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `${sign}${grouped},${frac}`;
}

export function parseQuantityInput(raw: string): number {
  const text = String(raw ?? "")
    .trim()
    .replace(/\s/g, "");
  if (!text) return Number.NaN;
  const normalized = text.includes(",")
    ? text.replace(/\./g, "").replace(",", ".")
    : text;
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? roundQuantity(parsed) : Number.NaN;
}

export function roundQuantity(value: number): number {
  const factor = 10 ** QUANTITY_DECIMALS;
  return Math.round(Number(value) * factor) / factor;
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-BR");
}

export function formatTaxId(value: string | null | undefined): string {
  const digits = (value || "").replace(/\D/g, "");
  if (digits.length === 14) {
    return digits.replace(
      /^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/,
      "$1.$2.$3/$4-$5",
    );
  }
  if (digits.length === 11) {
    return digits.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, "$1.$2.$3-$4");
  }
  return value || "—";
}

export function warehouse01BalanceHint(quantity: number | null | undefined): string {
  return `Saldo no almoxarifado 01: ${formatQuantity(quantity)}`;
}

export function itemTotal(quantity: number, unitPrice: number): number {
  return Number(quantity || 0) * Number(unitPrice || 0);
}

const NAME_PARTICLES = new Set(["de", "da", "do", "das", "dos", "e"]);

export function firstGivenName(value: string | null | undefined): string {
  const tokens = String(value ?? "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  for (const token of tokens) {
    if (!NAME_PARTICLES.has(token.toLowerCase())) {
      const hyphen = token.split("-")[0] || token;
      return hyphen.charAt(0).toUpperCase() + hyphen.slice(1).toLowerCase();
    }
  }
  return "—";
}

export function itemOriginLabel(item: {
  sales_order?: string | null;
  sales_order_item?: string | null;
}): string {
  const order = (item.sales_order || "").trim();
  if (!order) return "Avulso";
  const line = (item.sales_order_item || "").trim();
  return line ? `PV ${order}/${line}` : `PV ${order}`;
}
