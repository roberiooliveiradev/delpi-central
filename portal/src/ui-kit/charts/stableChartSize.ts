/** Minimum useful host size (px) — below this the chart is still measuring. */
export const STABLE_CHART_MIN_SIZE_PX = 8;

/**
 * Minimum delta (px) to accept a resize — rejects 1px jitter that triggers
 * React #185 in Recharts when the portal sidebar resizes `.main-area`.
 */
export const STABLE_CHART_SIZE_EPSILON_PX = 2;

/**
 * Accept a new size only when the delta is ≥ epsilon.
 * Avoids host↔chart feedback loops with Recharts ResponsiveContainer.
 */
export function shouldAcceptMeasuredSize(
  prev: { w: number; h: number } | null,
  next: { w: number; h: number },
  epsilonPx = STABLE_CHART_SIZE_EPSILON_PX,
): boolean {
  if (next.w < STABLE_CHART_MIN_SIZE_PX || next.h < STABLE_CHART_MIN_SIZE_PX) {
    return false;
  }
  if (!prev) return true;
  return Math.abs(prev.w - next.w) >= epsilonPx || Math.abs(prev.h - next.h) >= epsilonPx;
}
