export function toInputDate(value: string | null | undefined) {
  return value ? String(value).slice(0, 10) : "";
}

// Use the browser's local calendar date, not UTC, to avoid one-day shifts.
export function localInputDate(now = new Date()): string {
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function initialExpenseDate(
  savedExpenseDate: string | null | undefined,
  reportPeriodStart: string | null | undefined,
  now = new Date(),
): string {
  return toInputDate(savedExpenseDate) || toInputDate(reportPeriodStart) || localInputDate(now);
}

export function isSameMonth(value: string | null | undefined, now = new Date()) {
  if (!value) return false;
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  return String(value).startsWith(`${year}-${month}`);
}
