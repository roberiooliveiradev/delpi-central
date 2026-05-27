import { COMMERCIAL_ROL_SERIES_LABELS } from "../constants/commercialIndicators";
import { downloadCsv } from "./csv";

export function downloadRolSeriesCsv(
  filename: string,
  points: {
    periodo: string;
    rolMatrix: number;
    rolBranch: number;
  }[]
): void {
  if (points.length === 0) return;

  downloadCsv(
    filename,
    [
      "Período",
      COMMERCIAL_ROL_SERIES_LABELS.filial01,
      COMMERCIAL_ROL_SERIES_LABELS.filial02,
    ],
    points.map((point) => [
      point.periodo,
      String(point.rolMatrix),
      String(point.rolBranch),
    ])
  );
}
