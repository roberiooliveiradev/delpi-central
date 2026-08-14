export const LOOKBACK_MONTHS = 12;

function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

export function formatIsoDate(date: Date): string {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
}

function startOfDay(referenceDate: Date): Date {
  return new Date(referenceDate.getFullYear(), referenceDate.getMonth(), referenceDate.getDate());
}

export function getThisMonthRange(referenceDate = new Date()): {
  startDate: string;
  endDate: string;
} {
  const end = startOfDay(referenceDate);
  const start = new Date(end.getFullYear(), end.getMonth(), 1);
  return { startDate: formatIsoDate(start), endDate: formatIsoDate(end) };
}

export function getLast30DaysRange(referenceDate = new Date()): {
  startDate: string;
  endDate: string;
} {
  const end = startOfDay(referenceDate);
  const start = new Date(end);
  start.setDate(start.getDate() - 29);
  return { startDate: formatIsoDate(start), endDate: formatIsoDate(end) };
}

export function getLast6MonthsRange(referenceDate = new Date()): {
  startDate: string;
  endDate: string;
} {
  const end = startOfDay(referenceDate);
  const start = new Date(end.getFullYear(), end.getMonth() - 5, 1);
  return { startDate: formatIsoDate(start), endDate: formatIsoDate(end) };
}

export function getLast12MonthsRange(referenceDate = new Date()): {
  startDate: string;
  endDate: string;
} {
  const end = startOfDay(referenceDate);
  const start = new Date(end.getFullYear(), end.getMonth() - 11, 1);
  return { startDate: formatIsoDate(start), endDate: formatIsoDate(end) };
}

export function lookbackFloorIso(referenceDate = new Date()): string {
  const end = startOfDay(referenceDate);
  const start = new Date(end);
  start.setMonth(start.getMonth() - LOOKBACK_MONTHS);
  return formatIsoDate(start);
}

export function parseIsoDate(value: string): Date | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value.trim());
  if (!match) return null;
  const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  if (Number.isNaN(date.getTime())) return null;
  if (formatIsoDate(date) !== value.trim()) return null;
  return date;
}

export function validatePeriodRange(startDate: string, endDate: string): string | null {
  const start = parseIsoDate(startDate);
  const end = parseIsoDate(endDate);
  if (!start || !end) {
    return "Informe datas válidas.";
  }
  if (start > end) {
    return "A data inicial não pode ser maior que a data final.";
  }
  const months =
    (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth()) + 1;
  if (months > LOOKBACK_MONTHS) {
    return `Período máximo permitido: ${LOOKBACK_MONTHS} meses.`;
  }
  return null;
}

export type QuickRangePreset = "thisMonth" | "30d" | "6m" | "12m" | "all";

export function resolveQuickRangePreset(
  preset: QuickRangePreset,
  referenceDate = new Date(),
): { startDate: string; endDate: string } | null {
  switch (preset) {
    case "all":
      return null;
    case "30d":
      return getLast30DaysRange(referenceDate);
    case "6m":
      return getLast6MonthsRange(referenceDate);
    case "12m":
      return getLast12MonthsRange(referenceDate);
    case "thisMonth":
    default:
      return getThisMonthRange(referenceDate);
  }
}
