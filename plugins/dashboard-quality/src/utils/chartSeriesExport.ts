import { downloadCsv } from "./csv";

export function downloadChartSeriesCsv(
  filename: string,
  points: { periodo: string; value: number; valueLabel?: string }[]
): void {
  if (points.length === 0) return;

  const label = points[0]?.valueLabel ?? "Valor";

  downloadCsv(
    filename,
    ["Período", label],
    points.map((point) => [point.periodo, String(point.value)])
  );
}

export function downloadDualPpmSeriesCsv(
  filename: string,
  points: {
    periodo: string;
    ppmInternal: number;
    ppmExternal: number;
  }[]
): void {
  if (points.length === 0) return;

  downloadCsv(
    filename,
    ["Período", "PPM interno", "PPM externo"],
    points.map((point) => [
      point.periodo,
      String(point.ppmInternal),
      String(point.ppmExternal),
    ])
  );
}
