import type { TrendDirection } from "../types/indicators";

const DEFAULT_TOLERANCE = 0.09;

export function resolveScoreTrendDirection(
  points: ReadonlyArray<{ value: number }>,
  tolerance = DEFAULT_TOLERANCE,
): TrendDirection {
  if (points.length < 2) {
    return "stable";
  }

  const current = points[points.length - 1]!.value;
  const previous = points[points.length - 2]!.value;
  const delta = current - previous;

  if (delta > tolerance) {
    return "up";
  }
  if (delta < -tolerance) {
    return "down";
  }
  return "stable";
}

export function resolveIndicatorSparklineDirection(
  series: ReadonlyArray<{ value: number }>,
  fallback: TrendDirection,
): TrendDirection {
  if (series.length >= 2) {
    return resolveScoreTrendDirection(series);
  }

  return fallback;
}
