import { buildRolSeriesPayload, exportTableFormat } from "../export";
import type { RolSeriesPoint } from "../hooks/useCommercialRolSeries";

/** @deprecated Preferir `buildRolSeriesPayload` + `exportTableFormat`. */
export function downloadRolSeriesCsv(
  _filename: string,
  points: RolSeriesPoint[],
): void {
  if (points.length === 0) return;

  exportTableFormat(buildRolSeriesPayload(points), "csv");
}
