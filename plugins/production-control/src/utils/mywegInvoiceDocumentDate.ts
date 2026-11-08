/** Data de documento ISO (YYYY-MM-DD) do dia civil anterior (D-1), no fuso local. */
export function previousCalendarDayIso(now: Date = new Date()): string {
  const day = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
  const y = day.getFullYear();
  const m = String(day.getMonth() + 1).padStart(2, "0");
  const d = String(day.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}
