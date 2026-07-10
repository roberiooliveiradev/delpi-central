import type { ChartGranularity } from "../types/chartGranularity";

function parseIsoDate(value: string): Date | null {
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return null;

  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const date = new Date(year, month - 1, day);

  if (
    date.getFullYear() !== year ||
    date.getMonth() !== month - 1 ||
    date.getDate() !== day
  ) {
    return null;
  }

  return date;
}

export function suggestChartGranularity(
  dateStart?: string,
  dateEnd?: string,
): ChartGranularity {
  if (!dateStart || !dateEnd) return "month";

  const start = parseIsoDate(dateStart);
  const end = parseIsoDate(dateEnd);

  if (!start || !end || start > end) return "month";

  const diffDays =
    Math.floor((end.getTime() - start.getTime()) / 86_400_000) + 1;

  if (diffDays <= 31) return "day";
  if (diffDays <= 120) return "week";
  if (diffDays <= 730) return "month";
  return "year";
}
