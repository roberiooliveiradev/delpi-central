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
  /** Índices de rótulos X sem colisão (inclui último só se couber). */
  visibleXLabelIndices: number[];
  toX: (index: number, count: number) => number;
  toY: (value: number) => number;
};

export type BuildSeriesChartLayoutInput = {
  points: SeriesChartPoint[];
  showXAxisLabels: boolean;
  showXAxisTitle: boolean;
  /** ViewBox dinâmico (ResizeObserver). Default: constantes SERIES_CHART_VIEW_*. */
  viewW?: number;
  viewH?: number;
};

const BASE_MARGIN: SeriesChartMargin = {
  top: 12,
  right: 14,
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

/**
 * Índices de rótulos X sem empilhar o último sobre o penúltimo tick do step.
 * Se o último ponto colide com o penúltimo visível, substitui o penúltimo pelo último.
 */
export function resolveVisibleXLabelIndices(count: number, step: number): number[] {
  if (count <= 0) return [];
  if (count === 1) return [0];
  const safeStep = Math.max(1, step);
  const indices: number[] = [];
  for (let i = 0; i < count; i += safeStep) {
    indices.push(i);
  }
  const last = count - 1;
  if (indices[indices.length - 1] === last) return indices;
  const prev = indices[indices.length - 1] ?? 0;
  if (last - prev >= safeStep) {
    indices.push(last);
    return indices;
  }
  // Colisão: trocar o penúltimo tick pelo último ponto (Excel-like).
  if (indices.length === 1) {
    indices.push(last);
  } else {
    indices[indices.length - 1] = last;
  }
  return indices;
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

  const viewW = Math.max(120, input.viewW ?? SERIES_CHART_VIEW_W);
  const viewH = Math.max(80, input.viewH ?? SERIES_CHART_VIEW_H);

  const labels = input.points.map((point, index) => String(point.label ?? index + 1));
  const plotWProbe = Math.max(40, viewW - BASE_MARGIN.left - BASE_MARGIN.right);
  const xLabelStep = input.showXAxisLabels
    ? resolveXLabelStep(input.points.length, plotWProbe, labels)
    : 1;
  const xLabelsRotated = input.showXAxisLabels
    ? shouldRotateXLabels(input.points.length, xLabelStep, plotWProbe, labels)
    : false;
  const visibleXLabelIndices = input.showXAxisLabels
    ? resolveVisibleXLabelIndices(input.points.length, xLabelStep)
    : [];

  const margin: SeriesChartMargin = {
    ...BASE_MARGIN,
    bottom: resolveBottomMargin(input.showXAxisLabels, input.showXAxisTitle, xLabelsRotated),
  };

  const plotW = Math.max(1, viewW - margin.left - margin.right);
  const plotH = Math.max(1, viewH - margin.top - margin.bottom);

  const toX = (index: number, count: number) =>
    margin.left + (count > 1 ? (index / (count - 1)) * plotW : plotW / 2);
  const toY = (value: number) => margin.top + plotH - ((value - axisMin) / axisRange) * plotH;

  return {
    viewW,
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
    visibleXLabelIndices,
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
