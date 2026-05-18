import type { PpmSeriesPoint } from "../hooks/usePpmChartSeries";

export type DualPpmSeriesPoint = {
  periodo: string;
  sortKey: string;
  dateStart: string;
  dateEnd: string;
  ppmInternal: number;
  ppmExternal: number;
};

export function mergePpmSeries(
  internal: PpmSeriesPoint[],
  external: PpmSeriesPoint[]
): DualPpmSeriesPoint[] {
  const byKey = new Map<string, DualPpmSeriesPoint>();

  for (const point of internal) {
    byKey.set(point.sortKey, {
      periodo: point.periodo,
      sortKey: point.sortKey,
      dateStart: point.dateStart,
      dateEnd: point.dateEnd,
      ppmInternal: point.ppm,
      ppmExternal: 0,
    });
  }

  for (const point of external) {
    const existing = byKey.get(point.sortKey);

    if (existing) {
      existing.ppmExternal = point.ppm;
      continue;
    }

    byKey.set(point.sortKey, {
      periodo: point.periodo,
      sortKey: point.sortKey,
      dateStart: point.dateStart,
      dateEnd: point.dateEnd,
      ppmInternal: 0,
      ppmExternal: point.ppm,
    });
  }

  return Array.from(byKey.values()).sort((a, b) =>
    a.sortKey.localeCompare(b.sortKey)
  );
}
