import type { MultiTypeSeriesSpec } from "./MultiTypeSeriesChart";

/**
 * Apply persisted series fill overrides onto host default series specs.
 * Trend lines in MultiTypeSeriesChart inherit `source.fill` after this merge.
 */
export function applySeriesFillPreferences(
  series: ReadonlyArray<MultiTypeSeriesSpec>,
  seriesFills?: Record<string, string> | null,
): MultiTypeSeriesSpec[] {
  if (!seriesFills || Object.keys(seriesFills).length === 0) {
    return series.map((entry) => ({ ...entry }));
  }
  return series.map((entry) => {
    const override = seriesFills[entry.dataKey];
    if (typeof override !== "string") return { ...entry };
    const fill = override.trim();
    if (!fill) return { ...entry };
    return { ...entry, fill };
  });
}
