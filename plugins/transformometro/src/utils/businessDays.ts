/** Contagem de dias por mês/recorte (dias corridos por padrão). */

import { isNationalHoliday } from "./brazilNationalHolidays";

/** Quando true: só seg–sex e sem feriados nacionais. */
export const USE_ONLY_BUSINESS_DAYS = false;

export function isCountedDay(date: Date): boolean {
  if (!USE_ONLY_BUSINESS_DAYS) return true;
  const day = date.getDay();
  return day >= 1 && day <= 5 && !isNationalHoliday(date);
}

export function isBusinessDay(date: Date): boolean {
  return isCountedDay(date);
}

export function daysInMonth(year: number, month: number): number {
  return new Date(year, month, 0).getDate();
}

export function countDaysInRange(start: Date, end: Date): number {
  if (end < start) return 0;
  let total = 0;
  const cursor = new Date(start.getFullYear(), start.getMonth(), start.getDate());
  const limit = new Date(end.getFullYear(), end.getMonth(), end.getDate());
  while (cursor <= limit) {
    if (isCountedDay(cursor)) total += 1;
    cursor.setDate(cursor.getDate() + 1);
  }
  return total;
}

export function countBusinessDays(start: Date, end: Date): number {
  return countDaysInRange(start, end);
}

export function businessDaysInMonth(year: number, month: number): number {
  const lastDay = daysInMonth(year, month);
  return countDaysInRange(
    new Date(year, month - 1, 1),
    new Date(year, month - 1, lastDay)
  );
}

export function parseIsoDate(iso: string): Date {
  const [year, month, day] = iso.split("-").map(Number);
  return new Date(year, month - 1, day);
}

export function countDaysInFilterForMonth(
  year: number,
  month: number,
  dateStart: string,
  dateEnd: string
): number {
  const dim = daysInMonth(year, month);
  let total = 0;
  for (let day = 1; day <= dim; day += 1) {
    const iso = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    if (iso < dateStart || iso > dateEnd) continue;
    if (isCountedDay(parseIsoDate(iso))) total += 1;
  }
  return total;
}

export function countBusinessDaysInFilterForMonth(
  year: number,
  month: number,
  dateStart: string,
  dateEnd: string
): number {
  return countDaysInFilterForMonth(year, month, dateStart, dateEnd);
}
