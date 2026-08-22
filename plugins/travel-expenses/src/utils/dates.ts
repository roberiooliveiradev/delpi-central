export function toInputDate(value: string | null | undefined) {
  return value ? String(value).slice(0, 10) : "";
}

export function isSameMonth(value: string | null | undefined, now = new Date()) {
  if (!value) return false;
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  return String(value).startsWith(`${year}-${month}`);
}
