/**
 * Year-over-year helpers for Overview series overlays.
 * Calendar ISO dates YYYY-MM-DD — no timezone shift.
 */

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

function daysInMonth(year: number, month1to12: number): number {
  return new Date(Date.UTC(year, month1to12, 0)).getUTCDate();
}

export function shiftIsoDateByYears(isoDate: string, years: number): string {
  if (!ISO_DATE.test(isoDate) || !Number.isFinite(years)) return isoDate;
  const [y, m, d] = isoDate.split("-").map(Number);
  const targetYear = y + years;
  const maxDay = daysInMonth(targetYear, m);
  const day = Math.min(d, maxDay);
  return `${targetYear}-${String(m).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

export type PeriodDateRange = {
  from: string;
  to: string;
};

export function shiftPeriodRangeByYears(range: PeriodDateRange, years: number): PeriodDateRange {
  return {
    from: shiftIsoDateByYears(range.from, years),
    to: shiftIsoDateByYears(range.to, years),
  };
}

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
