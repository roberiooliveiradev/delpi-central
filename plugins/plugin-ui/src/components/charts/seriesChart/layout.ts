import {
  formatSeriesChartValue,
  resolveSeriesChartTicks,
  type SeriesChartKind,
  type SeriesChartOptions,
  type SeriesChartValueFormat,
  type SeriesChartPoint,
} from "../seriesChartOptions";
import type { ChartPartFrame } from "../seriesChartParts";

export const SERIES_CHART_VIEW_W = 400;
export const SERIES_CHART_VIEW_H = 220;

/** Inset interno do plot — folga para stroke/marcadores não colarem nem furarem o clip. */
export const SERIES_CHART_PLOT_INSET = 14;

/**
 * Escala de categoria no eixo X (padrão de mercado):
 * - `point` — linha/área/scatter: extremos nas bordas (d3.scalePoint / ECharts boundaryGap:false)
 * - `band` — coluna/barra: centro da banda (d3.scaleBand / ECharts boundaryGap:true / Excel)
 */
export type SeriesChartCategoryScale = "point" | "band";

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
  /** Escala X ativa — barras e rótulos devem concordar. */
  categoryScale: SeriesChartCategoryScale;
  ticks: number[];
  axisMin: number;
  axisMax: number;
  axisRange: number;
  xLabelStep: number;
  xLabelsRotated: boolean;
  /** Índices de rótulos X sem colisão (inclui último só se couber). */
  visibleXLabelIndices: number[];
  /** Âncora X da categoria: centro da banda (`band`) ou ponto (`point`). */
  toX: (index: number, count: number) => number;
  /** Início (esquerda) da banda de categoria — alinhado a `toX` em modo band. */
  categoryBandStart: (index: number, count: number) => number;
  /** Largura da banda de categoria. */
  categoryBandWidth: (count: number) => number;
  toY: (value: number) => number;
  /** Escala Y direita (séries com plotOn=secondary). */
  toYSecondary?: (value: number) => number;
  secondaryTicks?: number[];
  hasSecondaryAxis?: boolean;
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
  /**
   * Valores extras para escala Y (ex.: multi-série).
   * Quando presente, substitui os values de `points` no cálculo de ticks.
   */
  axisValues?: number[];
  /** Valores para eixo Y secundário (direita). */
  secondaryAxisValues?: number[];
  showXAxisLabels: boolean;
  showXAxisTitle: boolean;
  /** Reserva faixa esquerda para título Y rotacionado (evita clip no overflow do SVG). */
  showYAxisTitle?: boolean;
  /** ViewBox dinâmico (ResizeObserver). Default: constantes SERIES_CHART_VIEW_*. */
  viewW?: number;
  viewH?: number;
  /**
   * Padding de categoria no eixo X (% da largura do plot em cada lado).
   * Default 0: primeiro/último ponto alinhados às bordas do plot (como o zero no Y).
   */
  categoryPaddingPercent?: number;
  /**
   * Frame % do plotArea relativo ao viewBox (4H.6).
   * Quando `w`/`h` presentes, substitui as margens automáticas.
   */
  plotFrame?: ChartPartFrame | null;
  /** Fontes efetivas (px user units). Default: calibração histórica (eixo 9). */
  typography?: SeriesChartLayoutTypography | null;
  /**
   * Pizza / funil / radar: margens simétricas — o desenho fica no centro do plot-host,
   * sem gutters de eixo cartesiano (Y à esquerda, X embaixo).
   */
  centeredPlot?: boolean;
  /** Folga extra (px) quando rótulos ficam fora do anel/área (evita clip). */
  plotPadExtraPx?: number;
  /**
   * Escala de categoria X. Default `point`.
   * Tipos coluna/barra devem passar `band` (via `resolveSeriesChartCategoryScale`).
   */
  categoryScale?: SeriesChartCategoryScale;
};

/** Tipos que usam band scale no eixo X (barras centradas na categoria). */
export function resolveSeriesChartCategoryScale(
  chartType: SeriesChartKind | null | undefined,
): SeriesChartCategoryScale {
  switch (chartType) {
    case "bar":
    case "stacked_bar":
    case "histogram":
    case "waterfall":
    case "combo":
      return "band";
    default:
      return "point";
  }
}

/**
 * Geometria de coluna dentro da banda — mesma conta para paint e data labels.
 * Alinha ao centro retornado por `layout.toX` em modo `band`.
 */
export function resolveSeriesChartCategoryBarSlot(args: {
  layout: Pick<SeriesChartLayout, "categoryBandStart" | "categoryBandWidth">;
  categoryIndex: number;
  categoryCount: number;
  seriesIndex?: number;
  seriesCount?: number;
  padRatio?: number;
  fillRatio?: number;
}): { x: number; width: number; centerX: number } {
  const {
    layout,
    categoryIndex,
    categoryCount,
    seriesIndex = 0,
    seriesCount = 1,
    padRatio = 0.12,
    fillRatio = 0.8,
  } = args;
  const count = Math.max(1, categoryCount);
  const slotW = layout.categoryBandWidth(count);
  const bandStart = layout.categoryBandStart(categoryIndex, count);
  const groupPad = Math.min(slotW * padRatio, padRatio >= 0.15 ? 8 : 6);
  const usable = Math.max(slotW - groupPad * 2, 2);
  const seriesN = Math.max(1, seriesCount);
  const safeIndex = Math.min(Math.max(0, seriesIndex), seriesN - 1);
  const innerGap = seriesN > 1 ? Math.min(usable * 0.08, 3) : 0;
  const barW =
    seriesN > 1
      ? Math.max((usable - innerGap * (seriesN - 1)) / seriesN, 2)
      : Math.max(usable * fillRatio, 2);
  const clusterOffset = seriesN > 1 ? 0 : (usable - barW) / 2;
  const x = bandStart + groupPad + clusterOffset + safeIndex * (barW + innerGap);
  return { x, width: barW, centerX: x + barW / 2 };
}

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
  // Cap moderado: tipografia live no resize do bloco pode subir muito;
  // o piso do plot (`clampMarginsForUsablePlot`) é a defesa final.
  return Math.max(0.85, Math.min(2.75, axisFontSize / SERIES_CHART_LAYOUT_REF_AXIS_FONT));
}

/** Fração mínima do viewBox reservada ao plot (evita série clipada a ~1px). */
export const SERIES_CHART_MIN_PLOT_FRACTION = 0.38;

/** Piso absoluto do plot em user units. */
export const SERIES_CHART_MIN_PLOT_PX = 48;

/**
 * Comprime margens proporcionalmente quando o plot colapsaria.
 * Canônico para qualquer consumidor de `buildSeriesChartLayout` (TV / editor).
 */
export function clampMarginsForUsablePlot(
  margin: SeriesChartMargin,
  viewW: number,
  viewH: number,
  options?: { minPlotFraction?: number; minPlotPx?: number },
): SeriesChartMargin {
  const minFrac = options?.minPlotFraction ?? SERIES_CHART_MIN_PLOT_FRACTION;
  const minPx = options?.minPlotPx ?? SERIES_CHART_MIN_PLOT_PX;
  const minPlotW = Math.min(viewW, Math.max(minPx, Math.round(viewW * minFrac)));
  const minPlotH = Math.min(viewH, Math.max(minPx, Math.round(viewH * minFrac)));

  let { top, right, bottom, left } = margin;

  const shrinkAxis = (
    a: number,
    b: number,
    maxSum: number,
  ): [number, number] => {
    const sum = a + b;
    if (sum <= maxSum || sum <= 0) return [Math.max(0, a), Math.max(0, b)];
    const s = maxSum / sum;
    let nextA = Math.round(a * s);
    let nextB = Math.round(b * s);
    let over = nextA + nextB - maxSum;
    if (over > 0) {
      if (nextB >= over) nextB -= over;
      else {
        over -= nextB;
        nextB = 0;
        nextA = Math.max(0, nextA - over);
      }
    }
    return [nextA, nextB];
  };

  if (viewW - left - right < minPlotW) {
    [left, right] = shrinkAxis(left, right, Math.max(0, viewW - minPlotW));
  }
  if (viewH - top - bottom < minPlotH) {
    [top, bottom] = shrinkAxis(top, bottom, Math.max(0, viewH - minPlotH));
  }

  return { top, right, bottom, left };
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

/** Âncora de texto X — point nas bordas evita clip; band sempre no centro da categoria. */
export function resolveXLabelTextAnchor(
  index: number,
  count: number,
  rotated: boolean,
  categoryScale: SeriesChartCategoryScale = "point",
): "start" | "middle" | "end" {
  if (rotated) return "end";
  if (count <= 1) return "middle";
  if (categoryScale === "band") return "middle";
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

/** Faixa extra à esquerda para o título Y rotacionado (−90°). */
export function yAxisTitleGutterPx(axisTitleFontSize: number): number {
  const fs =
    axisTitleFontSize > 0 ? axisTitleFontSize : SERIES_CHART_LAYOUT_REF_AXIS_FONT;
  return Math.round(fs * 1.15);
}

/**
 * Âncora X do título Y: centro da faixa esquerda, com meia-caixa do glifo ≥ 2px
 * dentro do viewBox (overflow:hidden no SVG).
 */
export function resolveYAxisTitleAnchorX(
  marginLeft: number,
  titleFontSize: number,
): number {
  const fs = titleFontSize > 0 ? titleFontSize : SERIES_CHART_LAYOUT_REF_AXIS_FONT;
  const halfEm = fs * 0.55;
  const minX = halfEm + 2;
  const strip = Math.max(yAxisTitleGutterPx(fs), minX * 2);
  const centeredInStrip = strip / 2;
  const cappedByMargin = Math.max(minX, Math.min(marginLeft * 0.38, centeredInStrip));
  return Math.max(minX, cappedByMargin);
}

function resolveLeftMarginWithYTitle(
  showYAxisTitle: boolean,
  left: number,
  axisTitleFontSize: number,
): number {
  if (!showYAxisTitle) return left;
  return left + yAxisTitleGutterPx(axisTitleFontSize);
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
  const values =
    input.axisValues && input.axisValues.length > 0
      ? input.axisValues.map((value) => Number(value))
      : input.points.map((point) => Number(point.value));
  const dataMin = Math.min(...values);
  const dataMax = Math.max(...values);
  const ticks = resolveSeriesChartTicks(dataMin, dataMax);
  const axisMin = Math.min(ticks[0] ?? dataMin, dataMin);
  const axisMax = Math.max(ticks[ticks.length - 1] ?? dataMax, dataMax);
  const axisRange = Math.max(axisMax - axisMin, 1e-6);

  const secondaryValues = (input.secondaryAxisValues ?? [])
    .map((value) => Number(value))
    .filter((value) => Number.isFinite(value));
  const hasSecondaryAxis = secondaryValues.length > 0;
  const secondaryTicks = hasSecondaryAxis
    ? resolveSeriesChartTicks(Math.min(...secondaryValues), Math.max(...secondaryValues))
    : undefined;
  const secondaryDataMin = hasSecondaryAxis ? Math.min(...secondaryValues) : 0;
  const secondaryDataMax = hasSecondaryAxis ? Math.max(...secondaryValues) : 1;
  const secondaryMin = Math.min(secondaryTicks?.[0] ?? secondaryDataMin, secondaryDataMin);
  const secondaryMax = Math.max(
    secondaryTicks?.[secondaryTicks.length - 1] ?? secondaryDataMax,
    secondaryDataMax,
  );
  const secondaryRange = Math.max(secondaryMax - secondaryMin, 1e-6);

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
  const showYAxisTitle = Boolean(input.showYAxisTitle);
  const cartesianAutoMargin: SeriesChartMargin = {
    top: baseMargin.top,
    left: resolveLeftMarginWithYTitle(showYAxisTitle, sides.left, axisTitleFontSize),
    right: Math.max(
      sides.right,
      hasSecondaryAxis ? Math.round(axisFontSize * 3.2) + 10 : sides.right,
    ),
    bottom: resolveBottomMargin(
      input.showXAxisLabels,
      input.showXAxisTitle,
      xLabelsRotated,
      baseMargin,
      axisFontSize,
      axisTitleFontSize,
    ),
  };
  const minLeftForYTitle = showYAxisTitle
    ? yAxisTitleGutterPx(axisTitleFontSize) + Math.round(axisFontSize * 2.6)
    : 0;
  const centeredPad = Math.max(
    8,
    Math.round(Math.min(viewW, viewH) * 0.045) + Math.max(0, input.plotPadExtraPx ?? 0),
  );
  const centeredAutoMargin: SeriesChartMargin = {
    top: centeredPad,
    right: centeredPad,
    bottom: centeredPad,
    left: centeredPad,
  };
  const autoMargin = input.centeredPlot ? centeredAutoMargin : cartesianAutoMargin;
  const margin: SeriesChartMargin = clampMarginsForUsablePlot(
    framedEarly
      ? {
          ...framedEarly,
          left: Math.max(framedEarly.left, minLeftForYTitle),
          right: Math.max(
            framedEarly.right,
            !input.centeredPlot && hasSecondaryAxis
              ? Math.round(axisFontSize * 3.2) + 10
              : framedEarly.right,
          ),
        }
      : autoMargin,
    viewW,
    viewH,
  );

  const plotW = Math.max(1, viewW - margin.left - margin.right);
  const plotH = Math.max(1, viewH - margin.top - margin.bottom);
  const padPct = Math.max(0, Math.min(40, input.categoryPaddingPercent ?? 0));
  // Cartesiano: inset 0 por padrão (extremos no eixo Y / borda direita).
  // Plot centralizado (pizza/funil) mantém folga mínima para não colar na moldura.
  const insetFromPercent =
    padPct > 0
      ? Math.round((plotW * padPct) / 100)
      : input.centeredPlot
        ? SERIES_CHART_PLOT_INSET
        : 0;
  const plotInset =
    insetFromPercent > 0
      ? Math.min(Math.floor(Math.min(plotW, plotH) / 6), Math.max(4, insetFromPercent))
      : 0;
  const innerW = Math.max(1, plotW - 2 * plotInset);
  const categoryScale: SeriesChartCategoryScale = input.categoryScale ?? "point";

  const categoryBandWidth = (count: number) => {
    const n = Math.max(1, count);
    return innerW / n;
  };
  const categoryBandStart = (index: number, count: number) => {
    const n = Math.max(1, count);
    const i = Math.min(Math.max(0, index), n - 1);
    return margin.left + plotInset + (i / n) * innerW;
  };

  // point: extremos nas bordas (linha). band: centro de cada categoria (coluna).
  const toX = (index: number, count: number) => {
    if (categoryScale === "band") {
      const n = Math.max(1, count);
      const i = Math.min(Math.max(0, index), n - 1);
      return margin.left + plotInset + ((i + 0.5) / n) * innerW;
    }
    return count > 1
      ? margin.left + plotInset + (index / (count - 1)) * innerW
      : margin.left + plotW / 2;
  };
  const toY = (value: number) => {
    const t = Math.min(1, Math.max(0, (value - axisMin) / axisRange));
    return margin.top + (1 - t) * plotH;
  };
  const toYSecondary = hasSecondaryAxis
    ? (value: number) => {
        const t = Math.min(1, Math.max(0, (value - secondaryMin) / secondaryRange));
        return margin.top + (1 - t) * plotH;
      }
    : undefined;

  return {
    viewW,
    viewH,
    margin,
    plotW,
    plotH,
    plotInset,
    categoryScale,
    ticks,
    axisMin,
    axisMax,
    axisRange,
    xLabelStep,
    xLabelsRotated,
    visibleXLabelIndices,
    toX,
    categoryBandStart,
    categoryBandWidth,
    toY,
    ...(hasSecondaryAxis
      ? { toYSecondary, secondaryTicks, hasSecondaryAxis: true }
      : {}),
  };
}

export function resolveSeriesName(config: SeriesChartOptions): string {
  const title = config.title?.trim();
  return config.seriesName?.trim() || title || "Série";
}

export function formatChartTick(value: number, valueFormat: SeriesChartValueFormat): string {
  return formatSeriesChartValue(value, valueFormat);
}
