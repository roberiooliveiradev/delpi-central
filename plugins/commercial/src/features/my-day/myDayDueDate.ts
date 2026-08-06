function pad2(n: number): string {
  return String(n).padStart(2, "0");
}

/** Data local YYYY-MM-DD (default prazo = hoje). */
export function localDateInputValue(date = new Date()): string {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
}

/** Converte input date para ISO no fim do dia local (EOD). */
export function dueDateInputToIsoEod(dateStr: string): string {
  const [y, m, d] = dateStr.split("-").map((part) => Number(part));
  if (!y || !m || !d) return new Date().toISOString();
  return new Date(y, m - 1, d, 23, 59, 0, 0).toISOString();
}

/** Converte ISO / Date para input date local YYYY-MM-DD. */
export function isoToLocalDateInput(value?: string | null): string {
  if (!value) return localDateInputValue();
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return localDateInputValue();
  return localDateInputValue(date);
}

/** Adia +1 dia civil a partir do prazo atual (ou de agora se sem prazo). */
export function deferDueAtOneDay(dueAt?: string | null): string {
  const base = dueAt ? new Date(dueAt) : new Date();
  const next = Number.isNaN(base.getTime()) ? new Date() : base;
  next.setDate(next.getDate() + 1);
  next.setHours(23, 59, 0, 0);
  return next.toISOString();
}
