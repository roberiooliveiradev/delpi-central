/** Data de documento ISO (YYYY-MM-DD) do dia civil anterior (D-1), no fuso local. */
export function previousCalendarDayIso(now: Date = new Date()): string {
  const day = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
  return formatLocalIsoDate(day);
}

export function formatLocalIsoDate(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export function parseLocalIsoDate(
  iso: string,
): { year: number; month: number; day: number } | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso.trim());
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  if (!year || month < 1 || month > 12 || day < 1 || day > 31) return null;
  return { year, month, day };
}

export type MonthGridCell = {
  iso: string;
  day: number;
  inMonth: boolean;
};

/** Grade do mês com semanas iniciando na segunda-feira (pt-BR). */
export function buildMonthGrid(year: number, month: number): MonthGridCell[] {
  const first = new Date(year, month - 1, 1);
  const firstWeekday = (first.getDay() + 6) % 7; // 0=segunda
  const start = new Date(year, month - 1, 1 - firstWeekday);
  const cells: MonthGridCell[] = [];
  for (let index = 0; index < 42; index += 1) {
    const current = new Date(
      start.getFullYear(),
      start.getMonth(),
      start.getDate() + index,
    );
    cells.push({
      iso: formatLocalIsoDate(current),
      day: current.getDate(),
      inMonth: current.getMonth() === month - 1,
    });
  }
  return cells;
}

export function shiftMonth(
  year: number,
  month: number,
  delta: number,
): { year: number; month: number } {
  const date = new Date(year, month - 1 + delta, 1);
  return { year: date.getFullYear(), month: date.getMonth() + 1 };
}
