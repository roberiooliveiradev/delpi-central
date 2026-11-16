import type { SeriesChartPoint } from "./seriesChartOptions";

/**
 * Seleção de ponto/categoria em gráficos de barras (U14R2 K1).
 * Props opcionais — sem elas o paint permanece idêntico.
 */
export type SeriesChartPointSelection = {
  onPointSelect?: (
    point: SeriesChartPoint | null,
    index: number | null,
  ) => void;
  /** Chave da categoria selecionada (default: `point.label` ou índice). */
  selectedPointKey?: string | null;
  pointKey?: (point: SeriesChartPoint, index: number) => string;
};

export function seriesChartPointKey(
  point: SeriesChartPoint,
  index: number,
  pointKey?: (point: SeriesChartPoint, index: number) => string,
): string {
  if (pointKey) return pointKey(point, index);
  const label = (point.label ?? "").trim();
  return label || String(index);
}
