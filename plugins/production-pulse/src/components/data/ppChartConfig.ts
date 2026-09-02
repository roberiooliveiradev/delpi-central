import type { ChartPoint } from "../../utils/detailDisplay";

export type PpReadingsChartVariant = "mini" | "detail";

/** Cor da série — alinhada a DECK_COLOR_ACCENT do plugin-ui. */
const PP_CHART_SERIES_COLOR = "#089bdb";

export const PP_READINGS_SERIES_KEY = "value";

export type PpComparativeChartPoint = {
  name: string;
  [key: string]: string | number;
};

export type PpComparativeChartSeries = {
  dataKey: string;
  name: string;
  color: string;
  fillOpacity?: number;
};

export function readingsToComparativeData(points: ChartPoint[]): PpComparativeChartPoint[] {
  return points.map((point) => ({
    name: point.label,
    [PP_READINGS_SERIES_KEY]: point.y,
  }));
}

export function buildPpReadingsChartSeries(isDark: boolean): PpComparativeChartSeries[] {
  return [
    {
      dataKey: PP_READINGS_SERIES_KEY,
      name: "Leitura",
      color: PP_CHART_SERIES_COLOR,
      fillOpacity: isDark ? 0.38 : 0.45,
    },
  ];
}

export function resolvePpReadingsChartHeight(
  variant: PpReadingsChartVariant,
  height?: number,
): number {
  if (height != null) return height;
  return variant === "mini" ? 220 : 280;
}

export function resolvePpReadingsChartYAxisWidth(variant: PpReadingsChartVariant): number {
  return variant === "mini" ? 52 : 64;
}

export function formatPpReadingsChartValue(value: number): string {
  return new Intl.NumberFormat("pt-BR", {
    maximumFractionDigits: 2,
  }).format(value);
}

/** @deprecated Mantido para compatibilidade — preferir readingsToComparativeData. */
export function readingsToSeriesPoints(points: ChartPoint[]) {
  return points.map((point) => ({
    label: point.label,
    value: point.y,
  }));
}
