import { PRODUCTION_OEE_SERIES_LABELS, PRODUCTION_OTD_SERIES_LABELS } from "../constants/productionIndicators";
import { downloadCsv } from "./csv";

export function downloadOeeSeriesCsv(
  filename: string,
  points: {
    periodo: string;
    oeeFilial01: number | null;
    oeeFilial02: number | null;
  }[]
): void {
  if (points.length === 0) return;

  downloadCsv(
    filename,
    [
      "Período",
      PRODUCTION_OEE_SERIES_LABELS.filial01,
      PRODUCTION_OEE_SERIES_LABELS.filial02,
    ],
    points.map((point) => [
      point.periodo,
      point.oeeFilial01 != null ? String(point.oeeFilial01) : "",
      point.oeeFilial02 != null ? String(point.oeeFilial02) : "",
    ])
  );
}

export function downloadOtdSeriesCsv(
  filename: string,
  points: {
    periodo: string;
    otdFilial01: number | null;
    otdFilial02: number | null;
  }[]
): void {
  if (points.length === 0) return;

  downloadCsv(
    filename,
    [
      "Período",
      PRODUCTION_OTD_SERIES_LABELS.filial01,
      PRODUCTION_OTD_SERIES_LABELS.filial02,
    ],
    points.map((point) => [
      point.periodo,
      point.otdFilial01 != null ? String(point.otdFilial01) : "",
      point.otdFilial02 != null ? String(point.otdFilial02) : "",
    ])
  );
}
