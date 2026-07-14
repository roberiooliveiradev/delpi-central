import {
  formatSeriesChartValue,
  resolveSeriesChartTicks,
  type SeriesChartOptions,
  type SeriesChartValueFormat,
  type SeriesChartPoint,
} from "../seriesChartOptions";
import type { ChartPartFrame } from "../seriesChartParts";

export const SERIES_CHART_VIEW_W = 400;
export const SERIES_CHART_VIEW_H = 220;

/** Inset interno do plot — folga para stroke/marcadores não colarem nem furarem o clip. */
export const SERIES_CHART_PLOT_INSET = 14;

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
  /** Inset usado em toX/toY (marcadores dentro do plot). */
  plotInset: number;
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

/**
 * Tipografia efetiva dos eixos — usada para margens e densidade de rótulos.
 * Sem isso, resize global escala fontSize no modelo mas as margens ficam
 * calibradas para 9px e os itens internos “quebram”.
 */
export type SeriesChartLayoutTypography = {
  axisFontSize?: number;
  axisTitleFontSize?: number;
};

export type BuildSeriesChartLayoutInput = {
  points: SeriesChartPoint[];
  showXAxisLabels: boolean;
  showXAxisTitle: boolean;
  /** ViewBox dinâmico (ResizeObserver). Default: constantes SERIES_CHART_VIEW_*. */
  viewW?: number;
  viewH?: number;
  /**
   * Padding de categoria no eixo X (% da largura do plot em cada lado).
   * Default: usa SERIES_CHART_PLOT_INSET como piso em px se omitido.
   */
  categoryPaddingPercent?: number;
  /**
   * Frame % do plotArea relativo ao viewBox (4H.6).
   * Quando `w`/`h` presentes, substitui as margens automáticas.
   */
  plotFrame?: ChartPartFrame | null;
  /** Fontes efetivas (px user units). Default: calibração histórica (eixo 9). */
  typography?: SeriesChartLayoutTypography | null;
};

/** Converte margens atuais do layout em frame % (materializar ao selecionar). */
export function chartPartFrameFromPlotLayout(layout: {
  viewW: number;
  viewH: number;
  margin: SeriesChartMargin;
  plotW: number;
  plotH: number;
}): ChartPartFrame {
  const viewW = Math.max(layout.viewW, 1);
  const viewH = Math.max(layout.viewH, 1);
  return {
    x: (layout.margin.left / viewW) * 100,
    y: (layout.margin.top / viewH) * 100,
    w: (layout.plotW / viewW) * 100,
    h: (layout.plotH / viewH) * 100,
  };
}

/** Margens a partir do frame % do plotArea; null se incompleto ou área inútil. */
export function marginsFromPlotFrame(
  frame: ChartPartFrame | null | undefined,
  viewW: number,
  viewH: number,
): SeriesChartMargin | null {
  if (frame == null || frame.w == null || frame.h == null) return null;
  if (frame.w < 15 || frame.h < 15) return null;
  const left = (frame.x / 100) * viewW;
  const top = (frame.y / 100) * viewH;
  const plotW = (frame.w / 100) * viewW;
  const plotH = (frame.h / 100) * viewH;
  if (plotW < 24 || plotH < 24) return null;
  return {
    top,
    left,
    right: Math.max(0, viewW - left - plotW),
    bottom: Math.max(0, viewH - top - plotH),
  };
}

/** Margens calibradas para eixo a 9px (referência histórica). */
const BASE_MARGIN_AT_REF: SeriesChartMargin = {
  top: 22,
  right: 20,
  bottom: 30,
  left: 52,
};

/** Tamanho de eixo em que `BASE_MARGIN_AT_REF` foi medido. */
export const SERIES_CHART_LAYOUT_REF_AXIS_FONT = 9;

function resolveAxisFontSize(typography?: SeriesChartLayoutTypography | null): number {
  const fs = typography?.axisFontSize;
  if (fs != null && Number.isFinite(fs) && fs > 0) return fs;
  return SERIES_CHART_LAYOUT_REF_AXIS_FONT;
}

function resolveAxisTitleFontSize(typography?: SeriesChartLayoutTypography | null): number {
  const fs = typography?.axisTitleFontSize;
  if (fs != null && Number.isFinite(fs) && fs > 0) return fs;
  return resolveAxisFontSize(typography);
}

function marginScaleForAxisFont(axisFontSize: number): number {
  return Math.max(0.85, Math.min(5, axisFontSize / SERIES_CHART_LAYOUT_REF_AXIS_FONT));
}

function scaledBaseMargin(axisFontSize: number): SeriesChartMargin {
  const s = marginScaleForAxisFont(axisFontSize);
  return {
    top: Math.round(BASE_MARGIN_AT_REF.top * s),
    right: Math.round(BASE_MARGIN_AT_REF.right * s),
    bottom: Math.round(BASE_MARGIN_AT_REF.bottom * s),
    left: Math.round(BASE_MARGIN_AT_REF.left * s),
  };
}

/** Largura aproximada do rótulo em user units (proporcional ao font-size). */
export function estimateLabelWidth(label: string, axisFontSize = SERIES_CHART_LAYOUT_REF_AXIS_FONT): number {
  const fs = axisFontSize > 0 ? axisFontSize : SERIES_CHART_LAYOUT_REF_AXIS_FONT;
  return Math.max(label.length, 1) * fs * 0.55;
}

export function resolveXLabelStep(
  count: number,
  plotW: number,
  labels: string[],
  axisFontSize = SERIES_CHART_LAYOUT_REF_AXIS_FONT,
): number {
  if (count <= 1) return 1;
  const avgWidth =
    labels.reduce((sum, label) => sum + estimateLabelWidth(label, axisFontSize), 0) /
    Math.max(labels.length, 1);
  const slotWidth = Math.max(avgWidth + axisFontSize * 0.45, axisFontSize * 2.2);
  const maxVisible = Math.max(2, Math.floor(plotW / slotWidth));
  if (count <= maxVisible) return 1;
  return Math.ceil(count / maxVisible);
}

export function shouldRotateXLabels(
  count: number,
  step: number,
  plotW: number,
  labels: string[],
  axisFontSize = SERIES_CHART_LAYOUT_REF_AXIS_FONT,
): boolean {
  if (count <= 6) return false;
  const visibleCount = Math.ceil(count / step);
  const avgWidth =
    labels.reduce((sum, label) => sum + estimateLabelWidth(label, axisFontSize), 0) /
    Math.max(labels.length, 1);
  return visibleCount * (avgWidth + axisFontSize * 0.3) > plotW * 0.92;
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

/** Âncora de texto X nas bordas — evita cortar o primeiro/último rótulo. */
export function resolveXLabelTextAnchor(
  index: number,
  count: number,
  rotated: boolean,
): "start" | "middle" | "end" {
  if (rotated) return "end";
  if (count <= 1) return "middle";
  if (index === 0) return "start";
  if (index === count - 1) return "end";
  return "middle";
}

function resolveBottomMargin(
  showXAxisLabels: boolean,
  showXAxisTitle: boolean,
  xLabelsRotated: boolean,
  base: SeriesChartMargin,
  axisFontSize: number,
  axisTitleFontSize: number,
): number {
  let bottom = base.bottom;
  if (showXAxisLabels) {
    bottom += Math.round(axisFontSize * (xLabelsRotated ? 1.6 : 1.1));
  }
  if (showXAxisTitle) {
    bottom += Math.round(axisTitleFontSize * 1.15);
  }
  return bottom;
}

/** Margens laterais que cabem meia largura do 1º/último rótulo X + ticks Y. */
function resolveSideMargins(
  showXAxisLabels: boolean,
  labels: string[],
  visibleIndices: number[],
  base: SeriesChartMargin,
  axisFontSize: number,
): Pick<SeriesChartMargin, "left" | "right"> {
  let left = base.left;
  let right = base.right;
  if (!showXAxisLabels || labels.length === 0) {
    return { left, right };
  }
  const firstIdx = visibleIndices[0] ?? 0;
  const lastIdx = visibleIndices[visibleIndices.length - 1] ?? labels.length - 1;
  // Com textAnchor start/end nas bordas, basta folga pequena + inset.
  const firstPad = Math.min(
    Math.round(axisFontSize * 1.2),
    Math.ceil(estimateLabelWidth(labels[firstIdx] ?? "", axisFontSize) * 0.15),
  );
  const lastPad = Math.min(
    Math.round(axisFontSize * 2.2),
    Math.ceil(estimateLabelWidth(labels[lastIdx] ?? "", axisFontSize) * 0.35) +
      Math.round(axisFontSize * 0.3),
  );
  left = Math.max(left, base.left + firstPad);
  right = Math.max(right, base.right, lastPad);
  return { left, right };
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
  const axisFontSize = resolveAxisFontSize(input.typography);
  const axisTitleFontSize = resolveAxisTitleFontSize(input.typography);
  const baseMargin = scaledBaseMargin(axisFontSize);

  const labels = input.points.map((point, index) => String(point.label ?? index + 1));
  const framedEarly = marginsFromPlotFrame(input.plotFrame, viewW, viewH);
  const plotWProbe = Math.max(
    40,
    framedEarly
      ? viewW - framedEarly.left - framedEarly.right
      : viewW - baseMargin.left - baseMargin.right,
  );
  const xLabelStep = input.showXAxisLabels
    ? resolveXLabelStep(input.points.length, plotWProbe, labels, axisFontSize)
    : 1;
  const xLabelsRotated = input.showXAxisLabels
    ? shouldRotateXLabels(input.points.length, xLabelStep, plotWProbe, labels, axisFontSize)
    : false;
  const visibleXLabelIndices = input.showXAxisLabels
    ? resolveVisibleXLabelIndices(input.points.length, xLabelStep)
    : [];

  const sides = resolveSideMargins(
    input.showXAxisLabels,
    labels,
    visibleXLabelIndices,
    baseMargin,
    axisFontSize,
  );
  const autoMargin: SeriesChartMargin = {
    top: baseMargin.top,
    left: sides.left,
    right: sides.right,
    bottom: resolveBottomMargin(
      input.showXAxisLabels,
      input.showXAxisTitle,
      xLabelsRotated,
      baseMargin,
      axisFontSize,
      axisTitleFontSize,
    ),
  };
  const margin: SeriesChartMargin = framedEarly ?? autoMargin;

  const plotW = Math.max(1, viewW - margin.left - margin.right);
  const plotH = Math.max(1, viewH - margin.top - margin.bottom);
  const padPct = Math.max(0, Math.min(40, input.categoryPaddingPercent ?? 0));
  const insetFromPercent =
    padPct > 0 ? Math.round((plotW * padPct) / 100) : SERIES_CHART_PLOT_INSET;
  const plotInset = Math.min(
    Math.floor(Math.min(plotW, plotH) / 6),
    Math.max(4, insetFromPercent),
  );
  const innerW = Math.max(1, plotW - 2 * plotInset);
  const innerH = Math.max(1, plotH - 2 * plotInset);

  const toX = (index: number, count: number) =>
    margin.left + plotInset + (count > 1 ? (index / (count - 1)) * innerW : innerW / 2);
  const toY = (value: number) => {
    const t = Math.min(1, Math.max(0, (value - axisMin) / axisRange));
    return margin.top + plotInset + (1 - t) * innerH;
  };

  return {
    viewW,
    viewH,
    margin,
    plotW,
    plotH,
    plotInset,
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
