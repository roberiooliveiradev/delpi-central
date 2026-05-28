export function getTodayInputValue(): string {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const day = String(today.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function getFirstDayOfMonthInputValue(reference = new Date()): string {
  const year = reference.getFullYear();
  const month = String(reference.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}-01`;
}

export function formatDisplayDate(value: string | null | undefined): string {
  if (!value) return "—";
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return value;
  return `${match[3]}/${match[2]}/${match[1]}`;
}

export function formatPeriodLabel(dateStart: string, dateEnd: string): string {
  return `${formatDisplayDate(dateStart)} — ${formatDisplayDate(dateEnd)}`;
}

/** Rótulo curto para eixo de gráficos (dd/MM). */
export function formatChartAxisDate(value: string): string {
  const display = formatDisplayDate(value);
  if (display === "—") return value;
  return display.slice(0, 5);
}
