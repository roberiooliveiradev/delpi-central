import type { ChartPoint } from "../../utils/detailDisplay";

export type PpReadingsChartVariant = "mini" | "detail";
export type PpChartTheme = "light" | "dark";

export type PpReadingsChartOptions = {
  showTitle: boolean;
  showLegend: boolean;
  showAxes: boolean;
  showGrid: boolean;
  showVerticalGrid: boolean;
  showMarkers: boolean;
  markerMode: "last" | "all";
  smoothLines: boolean;
  areaFillGradient: boolean;
  categoryLabelFormat: "autoDate";
  categoryLabelOverflow: "skip";
  categoryLabelRotation: "auto";
  valueFormat: "number";
  categoryPaddingPercent: number;
  theme: PpChartTheme;
};

export type PpSeriesChartPoint = {
  label: string;
  value: number;
};

export function readingsToSeriesPoints(points: ChartPoint[]): PpSeriesChartPoint[] {
  return points.map((point) => ({
    label: point.label,
    value: point.y,
  }));
}

export function buildPpReadingsChartOptions(
  variant: PpReadingsChartVariant,
  theme: PpChartTheme,
): PpReadingsChartOptions {
  return {
    showTitle: false,
    showLegend: false,
    showAxes: true,
    showGrid: true,
    showVerticalGrid: false,
    showMarkers: true,
    markerMode: variant === "mini" ? "last" : "all",
    smoothLines: true,
    areaFillGradient: true,
    categoryLabelFormat: "autoDate",
    categoryLabelOverflow: "skip",
    categoryLabelRotation: "auto",
    valueFormat: "number",
    categoryPaddingPercent: 6,
    theme,
  };
}
