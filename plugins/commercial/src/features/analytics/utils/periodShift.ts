/**
 * Year-over-year helpers for analytics series overlays (Overview YoY).
 * Calendar ISO dates YYYY-MM-DD — no timezone shift (caller already uses SP ranges).
 */

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

function daysInMonth(year: number, month1to12: number): number {
  return new Date(Date.UTC(year, month1to12, 0)).getUTCDate();
}

/**
 * Shift an ISO calendar date by whole years.
 * Clamps day when the target month is shorter (e.g. 2024-02-29 → 2023-02-28).
 */
export function shiftIsoDateByYears(isoDate: string, years: number): string {
  if (!ISO_DATE.test(isoDate) || !Number.isFinite(years)) return isoDate;
  const [y, m, d] = isoDate.split("-").map(Number);
  const targetYear = y + years;
  const maxDay = daysInMonth(targetYear, m);
  const day = Math.min(d, maxDay);
  return `${targetYear}-${String(m).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

export type PeriodDateRange = {
  start_date: string;
  end_date: string;
};

/** Shift both ends of a filter range by `years` (typically -1 for prior year). */
export function shiftPeriodRangeByYears(
  range: PeriodDateRange,
  years: number,
): PeriodDateRange {
  return {
    start_date: shiftIsoDateByYears(range.start_date, years),
    end_date: shiftIsoDateByYears(range.end_date, years),
  };
}

/** YoY overlay is disabled for day buckets (2× up to 366 KPI calls). */
export function isPriorYearCompareAllowed(granularity: string): boolean {
  return granularity !== "day";
}

/**
 * Align prior-year points onto the current axis by bucket index.
 * Extra prior points are ignored; missing prior slots stay undefined on prior keys.
 */
export function mergeSeriesWithPriorYear<
  TCurrent extends Record<string, unknown>,
  TPrior extends Record<string, unknown>,
>(
  current: readonly TCurrent[],
  prior: readonly TPrior[],
  mapPriorFields: (priorPoint: TPrior | undefined) => Record<string, unknown>,
): Array<TCurrent & Record<string, unknown>> {
  return current.map((point, index) => ({
    ...point,
    ...mapPriorFields(prior[index]),
  }));
}
