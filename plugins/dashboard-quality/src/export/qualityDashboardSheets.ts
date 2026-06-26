import type { TableExportPayload } from "./types";
import { formatDecimal } from "../utils/format";

type PpmPoint = {
  periodo: string;
  ppm: number | null;
};

export function buildPpmSeriesExportPayload(
  title: string,
  points: PpmPoint[],
): TableExportPayload {
  return {
    title,
    columns: [
      { key: "periodo", label: "Período" },
      { key: "ppm", label: "PPM" },
    ],
    rows: points.map((point) => ({
      periodo: point.periodo,
      ppm: point.ppm != null ? formatDecimal(point.ppm) : "—",
    })),
  };
}

export function formatQualityKpiValue(
  value: number | null | undefined,
  formatter: (value: number) => string = formatDecimal,
): string {
  return value != null ? formatter(value) : "—";
}

export function formatQualityPercentKpi(
  value: number | null | undefined,
): string {
  return value != null ? formatDecimal(value) : "—";
}
