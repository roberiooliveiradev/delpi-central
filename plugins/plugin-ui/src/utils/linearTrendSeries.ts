/**
 * Ordinary least-squares linear trend for chart series (index as x).
 * Incomplete buckets (MTD etc.) can be excluded or weighted by period fraction.
 */

export type IncompleteBucketMode = "exclude" | "weightByFraction";

export type BuildLinearTrendOptions = {
  /**
   * How to treat buckets with `bucketFractions[i] < 1`.
   * Default `exclude` — omit from the fit (line still evaluated at that x).
   */
  incompleteBucketMode?: IncompleteBucketMode;
  /**
   * Parallel to `values`. `null`/`undefined`/≥1 = complete; (0,1) = partial.
   */
  bucketFractions?: ReadonlyArray<number | null | undefined>;
};

function resolveFraction(
  fractions: ReadonlyArray<number | null | undefined> | undefined,
  index: number,
): number {
  if (!fractions || index >= fractions.length) return 1;
  const raw = fractions[index];
  if (raw == null || !Number.isFinite(Number(raw))) return 1;
  return Math.min(1, Math.max(0, Number(raw)));
}

/**
 * Fraction of a calendar bucket elapsed as of `asOf` (inclusive dates).
 * Complete past buckets → 1; future → 0; current → days elapsed / span.
 */
export function resolveCalendarBucketFraction(
  dateStart: string | null | undefined,
  dateEnd: string | null | undefined,
  asOf: Date = new Date(),
): number {
  const startText = (dateStart || "").trim();
  const endText = (dateEnd || "").trim();
  if (!startText || !endText) return 1;
  const start = Date.parse(`${startText}T00:00:00`);
  const end = Date.parse(`${endText}T23:59:59`);
  if (!Number.isFinite(start) || !Number.isFinite(end) || end < start) return 1;
  const now = asOf.getTime();
  if (now >= end) return 1;
  if (now <= start) return 0;
  return (now - start) / (end - start);
}

export function buildLinearTrendValues(
  values: ReadonlyArray<number | null | undefined>,
  options?: BuildLinearTrendOptions,
): (number | null)[] {
  const mode = options?.incompleteBucketMode ?? "exclude";
  const fractions = options?.bucketFractions;

  const points: { x: number; y: number }[] = [];
  for (let i = 0; i < values.length; i += 1) {
    const raw = values[i];
    if (raw == null || !Number.isFinite(Number(raw))) continue;
    const fraction = resolveFraction(fractions, i);
    const incomplete = fraction < 1 - 1e-9;
    if (incomplete && mode === "exclude") {
      continue;
    }
    let y = Number(raw);
    if (incomplete && mode === "weightByFraction") {
      if (fraction <= 0) continue;
      y = y / fraction;
    }
    points.push({ x: i, y });
  }

  if (points.length < 2) {
    return values.map(() => null);
  }

  const n = points.length;
  let sumX = 0;
  let sumY = 0;
  let sumXY = 0;
  let sumXX = 0;
  for (const point of points) {
    sumX += point.x;
    sumY += point.y;
    sumXY += point.x * point.y;
    sumXX += point.x * point.x;
  }

  const denom = n * sumXX - sumX * sumX;
  if (denom === 0) {
    return values.map(() => null);
  }

  const slope = (n * sumXY - sumX * sumY) / denom;
  const intercept = (sumY - slope * sumX) / n;

  return values.map((_, index) => intercept + slope * index);
}

export function withLinearTrendField<T extends Record<string, unknown>>(
  rows: readonly T[],
  valueKey: keyof T & string,
  trendKey: string,
  options?: BuildLinearTrendOptions & {
    /** Row field with bucket fraction 0..1 (overrides options.bucketFractions). */
    fractionKey?: string;
  },
): Array<T & Record<string, number | null>> {
  const fractionKey = options?.fractionKey;
  const bucketFractions =
    options?.bucketFractions ??
    (fractionKey
      ? rows.map((row) => {
          const raw = row[fractionKey];
          if (typeof raw === "number") return raw;
          if (raw == null || raw === "") return null;
          const n = Number(raw);
          return Number.isFinite(n) ? n : null;
        })
      : undefined);

  const trend = buildLinearTrendValues(
    rows.map((row) => {
      const raw = row[valueKey];
      if (typeof raw === "number") return raw;
      if (raw == null || raw === "") return null;
      const n = Number(raw);
      return Number.isFinite(n) ? n : null;
    }),
    {
      incompleteBucketMode: options?.incompleteBucketMode,
      bucketFractions,
    },
  );
  return rows.map((row, index) => ({
    ...row,
    [trendKey]: trend[index] ?? null,
  }));
}
