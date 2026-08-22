import { copy } from "../content/copy";

const ISO_DATE = /^(\d{4})-(\d{2})-(\d{2})$/;

export function parseIsoDate(value: string): Date | null {
  const match = ISO_DATE.exec(value.trim());
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const date = new Date(year, month - 1, day);
  if (
    Number.isNaN(date.getTime()) ||
    date.getFullYear() !== year ||
    date.getMonth() !== month - 1 ||
    date.getDate() !== day
  ) {
    return null;
  }
  return date;
}

/** Fim inclusivo na UI → limite exclusivo da api-delpi inadimplência. */
export function toDelinquencyExclusiveEnd(endInclusive: string): string {
  const parsed = parseIsoDate(endInclusive);
  if (!parsed) return endInclusive;
  const next = new Date(parsed.getFullYear(), parsed.getMonth(), parsed.getDate() + 1);
  return formatIsoDate(next);
}

export function formatIsoDate(date: Date): string {
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${date.getFullYear()}-${month}-${day}`;
}

export function validateDelinquencyPeriodRange(
  startDate: string | null,
  endDate: string | null,
): string | null {
  if (!startDate && !endDate) return null;
  if (!startDate || !endDate) {
    return copy.delinquency.periodPartial;
  }
  const start = parseIsoDate(startDate);
  const end = parseIsoDate(endDate);
  if (!start || !end) {
    return copy.delinquency.periodInvalid;
  }
  if (start > end) {
    return copy.delinquency.periodInverted;
  }
  return null;
}
