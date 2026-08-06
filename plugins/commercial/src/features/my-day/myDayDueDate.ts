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
