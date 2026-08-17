export function formatCurrency(value: number | null | undefined): string {
  const amount = typeof value === "number" && Number.isFinite(value) ? value : 0;
  return amount.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function formatDate(value: string | null | undefined): string {
  if (!value?.trim()) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString("pt-BR");
}

export function formatDateTime(value: Date | null | undefined): string {
  if (!value) return "—";
  return value.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

export function normalizeCustomerStore(store: string): string {
  const value = store.trim();
  if (/^\d+$/.test(value)) {
    return value.padStart(2, "0");
  }
  return value;
}

export function customerKey(code: string, store: string): string {
  return `${code.trim()}|${normalizeCustomerStore(store)}`;
}
