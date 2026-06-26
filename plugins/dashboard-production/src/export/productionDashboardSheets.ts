import { PRODUCTION_OEE_SERIES_LABELS, PRODUCTION_OTD_SERIES_LABELS } from "../constants/productionIndicators";
import { formatPercent } from "../utils/format";
import type { TableExportPayload } from "./types";

type OeePoint = {
  periodo: string;
  oeeFilial01: number | null;
  oeeFilial02: number | null;
};

type OtdPoint = {
  periodo: string;
  otdFilial01: number | null;
  otdFilial02: number | null;
};

export function buildOeeSeriesExportPayload(points: OeePoint[]): TableExportPayload {
  return {
    title: "Evolução OEE",
    columns: [
      { key: "periodo", label: "Período" },
      { key: "oeeFilial01", label: PRODUCTION_OEE_SERIES_LABELS.filial01 },
      { key: "oeeFilial02", label: PRODUCTION_OEE_SERIES_LABELS.filial02 },
    ],
    rows: points.map((point) => ({
      periodo: point.periodo,
      oeeFilial01:
        point.oeeFilial01 != null ? formatPercent(point.oeeFilial01) : "—",
      oeeFilial02:
        point.oeeFilial02 != null ? formatPercent(point.oeeFilial02) : "—",
    })),
  };
}

export function buildOtdSeriesExportPayload(points: OtdPoint[]): TableExportPayload {
  return {
    title: "Evolução OTD",
    columns: [
      { key: "periodo", label: "Período" },
      { key: "otdFilial01", label: PRODUCTION_OTD_SERIES_LABELS.filial01 },
      { key: "otdFilial02", label: PRODUCTION_OTD_SERIES_LABELS.filial02 },
    ],
    rows: points.map((point) => ({
      periodo: point.periodo,
      otdFilial01:
        point.otdFilial01 != null ? formatPercent(point.otdFilial01) : "—",
      otdFilial02:
        point.otdFilial02 != null ? formatPercent(point.otdFilial02) : "—",
    })),
  };
}
