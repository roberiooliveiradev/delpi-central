/**
 * Ordinary least-squares linear trend for chart series (index as x).
 * Finite values contribute to the fit; output evaluates a + b*x for every index.
 */

export function buildLinearTrendValues(
  values: ReadonlyArray<number | null | undefined>,
): (number | null)[] {
  const points: { x: number; y: number }[] = [];
  for (let i = 0; i < values.length; i += 1) {
    const raw = values[i];
    if (raw == null || !Number.isFinite(Number(raw))) continue;
    points.push({ x: i, y: Number(raw) });
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

/**
 * Copies rows and adds a trend field from OLS over `valueKey`.
 */
export function withLinearTrendField<T extends Record<string, unknown>>(
  rows: readonly T[],
  valueKey: keyof T & string,
  trendKey: string,
): Array<T & Record<string, number | null>> {
  const trend = buildLinearTrendValues(
    rows.map((row) => {
      const raw = row[valueKey];
      if (typeof raw === "number") return raw;
      if (raw == null || raw === "") return null;
      const n = Number(raw);
      return Number.isFinite(n) ? n : null;
    }),
  );
  return rows.map((row, index) => ({
    ...row,
    [trendKey]: trend[index] ?? null,
  }));
}
