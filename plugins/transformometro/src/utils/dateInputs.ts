/** Normaliza datas da API (ISO ou YYYY-MM-DD) para `<input type="date">`. */
export function toDateInputValue(value?: string | null): string {
  if (!value) return "";
  const raw = String(value).trim();
  if (/^\d{4}-\d{2}-\d{2}/.test(raw)) return raw.slice(0, 10);
  return "";
}

/** Normaliza competência/mês (YYYY-MM ou data) para `<input type="month">`. */
export function toMonthInputValue(value?: string | null): string {
  if (!value) return "";
  const raw = String(value).trim();
  if (/^\d{4}-\d{2}-\d{2}/.test(raw)) return raw.slice(0, 7);
  if (/^\d{4}-\d{2}$/.test(raw)) return raw;
  return "";
}

export function optionalDateField(value: string): string | undefined {
  const trimmed = value.trim();
  return trimmed || undefined;
}

export function todayDateInput(): string {
  return new Date().toISOString().slice(0, 10);
}
