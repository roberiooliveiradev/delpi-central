import {
  formatSeriesChartValue,
  resolveSeriesChartTicks,
  type SeriesChartOptions,
  type SeriesChartValueFormat,
  type SeriesChartPoint,
} from "../seriesChartOptions";

export const SERIES_CHART_VIEW_W = 400;
export const SERIES_CHART_VIEW_H = 220;

export type SeriesChartMargin = {
  top: number;
  right: number;
  bottom: number;
  left: number;
};

export type SeriesChartLayout = {
  viewW: number;
  viewH: number;
  margin: SeriesChartMargin;
  plotW: number;
  plotH: number;
  ticks: number[];
  axisMin: number;
  axisMax: number;
  axisRange: number;
  xLabelStep: number;
  xLabelsRotated: boolean;
  toX: (index: number, count: number) => number;
  toY: (value: number) => number;
};

export type BuildSeriesChartLayoutInput = {
  points: SeriesChartPoint[];
  showXAxisLabels: boolean;
  showXAxisTitle: boolean;
};

const BASE_MARGIN: SeriesChartMargin = {
  top: 12,
  right: 12,
  bottom: 28,
  left: 52,
};

function estimateLabelWidth(label: string): number {
  return Math.max(label.length, 1) * 5.5;
}

export function resolveXLabelStep(count: number, plotW: number, labels: string[]): number {
  if (count <= 1) return 1;
  const avgWidth =
    labels.reduce((sum, label) => sum + estimateLabelWidth(label), 0) / Math.max(labels.length, 1);
  const slotWidth = Math.max(avgWidth + 6, 28);
  const maxVisible = Math.max(2, Math.floor(plotW / slotWidth));
  if (count <= maxVisible) return 1;
  return Math.ceil(count / maxVisible);
}

export function shouldRotateXLabels(count: number, step: number, plotW: number, labels: string[]): boolean {
  if (count <= 6) return false;
  const visibleCount = Math.ceil(count / step);
  const avgWidth =
    labels.reduce((sum, label) => sum + estimateLabelWidth(label), 0) / Math.max(labels.length, 1);
  return visibleCount * (avgWidth + 4) > plotW * 0.92;
}

function resolveBottomMargin(
  showXAxisLabels: boolean,
  showXAxisTitle: boolean,
  xLabelsRotated: boolean,
): number {
  let bottom = BASE_MARGIN.bottom;
  if (showXAxisLabels) {
    bottom += xLabelsRotated ? 22 : 14;
  }
  if (showXAxisTitle) {
    bottom += 12;
  }
  return bottom;
}

export function buildSeriesChartLayout(input: BuildSeriesChartLayoutInput): SeriesChartLayout {
  const values = input.points.map((point) => Number(point.value));
  const dataMin = Math.min(...values);
  const dataMax = Math.max(...values);
  const ticks = resolveSeriesChartTicks(dataMin, dataMax);
  const axisMin = ticks[0] ?? dataMin;
  const axisMax = ticks[ticks.length - 1] ?? dataMax;
  const axisRange = Math.max(axisMax - axisMin, 1e-6);

  const labels = input.points.map((point, index) => String(point.label ?? index + 1));
  const plotWProbe = SERIES_CHART_VIEW_W - BASE_MARGIN.left - BASE_MARGIN.right;
  const xLabelStep = input.showXAxisLabels
    ? resolveXLabelStep(input.points.length, plotWProbe, labels)
    : 1;
  const xLabelsRotated = input.showXAxisLabels
    ? shouldRotateXLabels(input.points.length, xLabelStep, plotWProbe, labels)
    : false;

  const margin: SeriesChartMargin = {
    ...BASE_MARGIN,
    bottom: resolveBottomMargin(input.showXAxisLabels, input.showXAxisTitle, xLabelsRotated),
  };

  const viewH = SERIES_CHART_VIEW_H;
  const plotW = SERIES_CHART_VIEW_W - margin.left - margin.right;
  const plotH = viewH - margin.top - margin.bottom;

  const toX = (index: number, count: number) =>
    margin.left + (count > 1 ? (index / (count - 1)) * plotW : plotW / 2);
  const toY = (value: number) => margin.top + plotH - ((value - axisMin) / axisRange) * plotH;

  return {
    viewW: SERIES_CHART_VIEW_W,
    viewH,
    margin,
    plotW,
    plotH,
    ticks,
    axisMin,
    axisMax,
    axisRange,
    xLabelStep,
    xLabelsRotated,
    toX,
    toY,
  };
}

export function resolveSeriesName(config: SeriesChartOptions): string {
  const title = config.title?.trim();
  return config.seriesName?.trim() || title || "Série";
}

export function formatChartTick(value: number, valueFormat: SeriesChartValueFormat): string {
  return formatSeriesChartValue(value, valueFormat);
}
