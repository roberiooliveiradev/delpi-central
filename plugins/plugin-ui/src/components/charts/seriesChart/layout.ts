import type { DisplayFormatSpec } from "../../../displayFormat";
import {
  formatSeriesChartCategoryLabel,
  formatSeriesChartValue,
  resolveSeriesChartTicks,
  resolveSeriesChartValueDomain,
  truncateSeriesChartCategoryLabel,
  type SeriesChartCategoryLabelFormat,
  type SeriesChartCategoryLabelOverflow,
  type SeriesChartCategoryLabelRotation,
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
 * Folga no extremo alto do eixo de valor (px).
 * Com inset 0 (linha/área nas bordas da categoria), sem isso a série no teto
 * cola no clipPath e o stroke/preenchimento parece «cortado».
 */
export const SERIES_CHART_VALUE_AXIS_GUTTER_PX = 8;

/**
 * Escala de categoria no eixo X (padrão de mercado):
 * - `point` — linha/área/scatter: extremos nas bordas (d3.scalePoint / ECharts boundaryGap:false)
 * - `band` — coluna/barra: centro da banda (d3.scaleBand / ECharts boundaryGap:true / Excel)
 */
export type SeriesChartCategoryScale = "point" | "band";

/** Orientação do plot: colunas (vertical) vs barras (horizontal). */
export type SeriesChartOrientation = "vertical" | "horizontal";

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
  /** `horizontal` = categoria no Y, valor no X (barras). */
  orientation: SeriesChartOrientation;
  ticks: number[];
  axisMin: number;
  axisMax: number;
  axisRange: number;
  xLabelStep: number;
  xLabelsRotated: boolean;
  /** Graus de rotação dos rótulos de categoria (0 = sem rotação). */
  categoryLabelRotationDeg: number;
  /** Overflow efetivo dos rótulos de categoria. */
  categoryLabelOverflow: SeriesChartCategoryLabelOverflow;
  /** Índices de rótulos X sem colisão (inclui último só se couber). */
  visibleXLabelIndices: number[];
  /** Âncora X da categoria: centro da banda (`band`) ou ponto (`point`). */
  toX: (index: number, count: number) => number;
  /** Início (esquerda) da banda de categoria — alinhado a `toX` em modo band. */
  categoryBandStart: (index: number, count: number) => number;
  /** Largura da banda de categoria. */
  categoryBandWidth: (count: number) => number;
  toY: (value: number) => number;
  /** Valor → X (só orientation=horizontal). */
  toValueX?: (value: number) => number;
  /** Início (topo) da banda de categoria no Y (horizontal). */
  categoryBandStartY?: (index: number, count: number) => number;
  /** Altura da banda de categoria (horizontal). */
  categoryBandHeight?: (count: number) => number;
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
  /**
   * Rótulos do eixo Y (valores no vertical; categorias no `horizontal_bar`).
   * Default `true` quando omitido — mantém compat com callers legados.
   */
  showYAxisLabels?: boolean;
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
   * Gutter interno para marcadores grandes (bubble): inset X + faixa Y
   * para centro±r caber no clipPath.
   */
  markerGutterPx?: number;
  /**
   * Escala de categoria X. Default `point`.
   * Tipos coluna/barra devem passar `band` (via `resolveSeriesChartCategoryScale`).
   */
  categoryScale?: SeriesChartCategoryScale;
  /** Orientação do plot. Default `vertical`. */
  orientation?: SeriesChartOrientation;
  /** Rotação dos rótulos de categoria. Default `auto`. */
  categoryLabelRotation?: SeriesChartCategoryLabelRotation;
  /** Overflow dos rótulos de categoria. Default `skip`. */
  categoryLabelOverflow?: SeriesChartCategoryLabelOverflow;
  /** Formato dos rótulos de categoria (já aplicados nos `points[].label` preferencialmente). */
  categoryLabelFormat?: SeriesChartCategoryLabelFormat;
  /** Spec canônico das categorias — mesma fonte dos ticks pintados. */
  displayCategoryFormat?: DisplayFormatSpec;
  valueFormat?: SeriesChartValueFormat;
  decimalPlaces?: number | null;
  /** Spec canônico dos valores — mesma fonte dos ticks pintados (evita cortar R$). */
  displayValueFormat?: DisplayFormatSpec;
};

/** Tipos que usam band scale no eixo de categoria. */
export function resolveSeriesChartCategoryScale(
  chartType: SeriesChartKind | null | undefined,
): SeriesChartCategoryScale {
  switch (chartType) {
    case "bar":
    case "horizontal_bar":
    case "stacked_bar":
    case "histogram":
    case "waterfall":
    case "combo":
      return "band";
    default:
      return "point";
  }
}

export function resolveSeriesChartOrientation(
  chartType: SeriesChartKind | null | undefined,
): SeriesChartOrientation {
  return chartType === "horizontal_bar" ? "horizontal" : "vertical";
}

/** Resolve graus de rotação a partir da option + heurística. */
export function resolveCategoryLabelRotationDeg(
  rotation: SeriesChartCategoryLabelRotation | undefined,
  autoRotate: boolean,
): number {
  if (rotation === 0) return 0;
  if (rotation === -45) return -45;
  if (rotation === -90) return -90;
  return autoRotate ? -38 : 0;
}

/**
 * Geometria de coluna/barra dentro da banda — mesma conta para paint e data labels.
 * Vertical: banda no X. Horizontal: banda no Y (`orientation === "horizontal"`).
 */
export function resolveSeriesChartCategoryBarSlot(args: {
  layout: Pick<
    SeriesChartLayout,
    | "categoryBandStart"
    | "categoryBandWidth"
    | "categoryBandStartY"
    | "categoryBandHeight"
    | "orientation"
  >;
  categoryIndex: number;
  categoryCount: number;
  seriesIndex?: number;
  seriesCount?: number;
  padRatio?: number;
  fillRatio?: number;
}): { x: number; y: number; width: number; height: number; centerX: number; centerY: number } {
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
  const seriesN = Math.max(1, seriesCount);
  const safeIndex = Math.min(Math.max(0, seriesIndex), seriesN - 1);

  if (layout.orientation === "horizontal" && layout.categoryBandStartY && layout.categoryBandHeight) {
    const slotH = layout.categoryBandHeight(count);
    const bandStart = layout.categoryBandStartY(categoryIndex, count);
    const groupPad = Math.min(slotH * padRatio, padRatio >= 0.15 ? 8 : 6);
    const usable = Math.max(slotH - groupPad * 2, 2);
    const innerGap = seriesN > 1 ? Math.min(usable * 0.08, 3) : 0;
    const barH =
      seriesN > 1
        ? Math.max((usable - innerGap * (seriesN - 1)) / seriesN, 2)
        : Math.max(usable * fillRatio, 2);
    const clusterOffset = seriesN > 1 ? 0 : (usable - barH) / 2;
    const y = bandStart + groupPad + clusterOffset + safeIndex * (barH + innerGap);
    return {
      x: 0,
      y,
      width: 0,
      height: barH,
      centerX: 0,
      centerY: y + barH / 2,
    };
  }

  const slotW = layout.categoryBandWidth(count);
  const bandStart = layout.categoryBandStart(categoryIndex, count);
  const groupPad = Math.min(slotW * padRatio, padRatio >= 0.15 ? 8 : 6);
  const usable = Math.max(slotW - groupPad * 2, 2);
  const innerGap = seriesN > 1 ? Math.min(usable * 0.08, 3) : 0;
  const barW =
    seriesN > 1
      ? Math.max((usable - innerGap * (seriesN - 1)) / seriesN, 2)
      : Math.max(usable * fillRatio, 2);
  const clusterOffset = seriesN > 1 ? 0 : (usable - barW) / 2;
  const x = bandStart + groupPad + clusterOffset + safeIndex * (barW + innerGap);
  return {
    x,
    y: 0,
    width: barW,
    height: 0,
    centerX: x + barW / 2,
    centerY: 0,
  };
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
  // Cap alto o bastante para eixos ~40–48px (TV/editor); o piso do plot
  // (`clampMarginsForUsablePlot`) continua sendo a defesa final.
  return Math.max(0.85, Math.min(5.5, axisFontSize / SERIES_CHART_LAYOUT_REF_AXIS_FONT));
}

/** Fração mínima do viewBox reservada ao plot (evita série clipada a ~1px). */
export const SERIES_CHART_MIN_PLOT_FRACTION = 0.38;

/** Piso absoluto do plot em user units. */
export const SERIES_CHART_MIN_PLOT_PX = 48;

/**
 * Comprime margens quando o plot colapsaria.
 * Canônico para qualquer consumidor de `buildSeriesChartLayout` (TV / editor).
 *
 * `preferShrinkRight` / `preferShrinkTop`: encolhe primeiro a margem oposta aos
 * rótulos (direita / topo) para não “comer” o gutter de categoria / eixo X.
 */
export function clampMarginsForUsablePlot(
  margin: SeriesChartMargin,
  viewW: number,
  viewH: number,
  options?: {
    minPlotFraction?: number;
    minPlotPx?: number;
    preferShrinkRight?: boolean;
    preferShrinkTop?: boolean;
  },
): SeriesChartMargin {
  const minFrac = options?.minPlotFraction ?? SERIES_CHART_MIN_PLOT_FRACTION;
  const minPx = options?.minPlotPx ?? SERIES_CHART_MIN_PLOT_PX;
  const minPlotW = Math.min(viewW, Math.max(minPx, Math.round(viewW * minFrac)));
  const minPlotH = Math.min(viewH, Math.max(minPx, Math.round(viewH * minFrac)));

  let { top, right, bottom, left } = margin;

  const shrinkProportional = (
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

  /** Encolhe `flexible` primeiro; só então `protectedSide`. */
  const shrinkPreferFlexible = (
    protectedSide: number,
    flexible: number,
    maxSum: number,
  ): [number, number] => {
    const sum = protectedSide + flexible;
    if (sum <= maxSum || sum <= 0) {
      return [Math.max(0, protectedSide), Math.max(0, flexible)];
    }
    const excess = sum - maxSum;
    if (flexible >= excess) {
      return [Math.max(0, protectedSide), Math.max(0, flexible - excess)];
    }
    return [Math.max(0, protectedSide - (excess - flexible)), 0];
  };

  if (viewW - left - right < minPlotW) {
    const maxSum = Math.max(0, viewW - minPlotW);
    [left, right] = options?.preferShrinkRight
      ? shrinkPreferFlexible(left, right, maxSum)
      : shrinkProportional(left, right, maxSum);
  }
  if (viewH - top - bottom < minPlotH) {
    const maxSum = Math.max(0, viewH - minPlotH);
    if (options?.preferShrinkTop) {
      [bottom, top] = shrinkPreferFlexible(bottom, top, maxSum);
    } else {
      [top, bottom] = shrinkProportional(top, bottom, maxSum);
    }
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

/**
 * Margem esquerda mínima para categorias no `horizontal_bar`
 * (`textAnchor="end"` em `margin.left - 6`).
 * Usa a largura estimada completa — sem reaplicar o fator 0.55.
 */
export function resolveHorizontalCategoryLabelLeftPad(
  labels: string[],
  axisFontSize: number,
  options?: { paintGapPx?: number },
): number {
  const fs = axisFontSize > 0 ? axisFontSize : SERIES_CHART_LAYOUT_REF_AXIS_FONT;
  const gap = options?.paintGapPx ?? 8;
  if (labels.length === 0) {
    return Math.round(fs * 3.5) + gap;
  }
  const maxLabel = Math.max(
    ...labels.map((label) => estimateLabelWidth(label, fs)),
    fs,
  );
  return Math.ceil(maxLabel + gap);
}

/**
 * Margem esquerda mínima para ticks de valor no eixo Y (orientação vertical).
 */
export function resolveValueAxisLabelLeftPad(
  tickLabels: string[],
  axisFontSize: number,
  options?: { paintGapPx?: number },
): number {
  const fs = axisFontSize > 0 ? axisFontSize : SERIES_CHART_LAYOUT_REF_AXIS_FONT;
  const gap = options?.paintGapPx ?? 8;
  if (tickLabels.length === 0) {
    return Math.round(fs * 2.6) + gap;
  }
  const maxLabel = Math.max(
    ...tickLabels.map((label) => estimateLabelWidth(label, fs)),
    fs,
  );
  return Math.ceil(maxLabel + gap);
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
  rotationDeg = 0,
): number {
  let bottom = base.bottom;
  if (showXAxisLabels) {
    const absRot = Math.abs(rotationDeg);
    const rotFactor = absRot >= 90 ? 2.4 : absRot >= 45 ? 2.0 : xLabelsRotated ? 1.6 : 1.1;
    bottom += Math.round(axisFontSize * rotFactor);
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
  const rawValues =
    input.axisValues && input.axisValues.length > 0
      ? input.axisValues.map((value) => Number(value))
      : input.points.map((point) => Number(point.value));
  const values = rawValues.filter((value) => Number.isFinite(value));
  const dataMin = values.length > 0 ? Math.min(...values) : 0;
  const dataMax = values.length > 0 ? Math.max(...values) : 1;
  const valueDomain = resolveSeriesChartValueDomain(dataMin, dataMax);
  const ticks = resolveSeriesChartTicks(valueDomain.min, valueDomain.max);
  const axisMin = Math.min(ticks[0] ?? valueDomain.min, valueDomain.min);
  const axisMax = Math.max(ticks[ticks.length - 1] ?? valueDomain.max, valueDomain.max);
  const axisRange = Math.max(axisMax - axisMin, 1e-6);

  const secondaryValues = (input.secondaryAxisValues ?? [])
    .map((value) => Number(value))
    .filter((value) => Number.isFinite(value));
  const hasSecondaryAxis = secondaryValues.length > 0;
  const secondaryDataMin = hasSecondaryAxis ? Math.min(...secondaryValues) : 0;
  const secondaryDataMax = hasSecondaryAxis ? Math.max(...secondaryValues) : 1;
  const secondaryDomain = resolveSeriesChartValueDomain(secondaryDataMin, secondaryDataMax);
  const secondaryTicks = hasSecondaryAxis
    ? resolveSeriesChartTicks(secondaryDomain.min, secondaryDomain.max)
    : undefined;
  const secondaryMin = Math.min(secondaryTicks?.[0] ?? secondaryDomain.min, secondaryDomain.min);
  const secondaryMax = Math.max(
    secondaryTicks?.[secondaryTicks.length - 1] ?? secondaryDomain.max,
    secondaryDomain.max,
  );
  const secondaryRange = Math.max(secondaryMax - secondaryMin, 1e-6);

  const viewW = Math.max(120, input.viewW ?? SERIES_CHART_VIEW_W);
  const viewH = Math.max(80, input.viewH ?? SERIES_CHART_VIEW_H);
  const axisFontSize = resolveAxisFontSize(input.typography);
  const axisTitleFontSize = resolveAxisTitleFontSize(input.typography);
  const baseMargin = scaledBaseMargin(axisFontSize);

  const orientation: SeriesChartOrientation = input.orientation ?? "vertical";
  const categoryLabelOverflow: SeriesChartCategoryLabelOverflow =
    input.categoryLabelOverflow ?? "skip";
  const labels = input.points.map((point, index) => String(point.label ?? index + 1));
  const framedEarly = marginsFromPlotFrame(input.plotFrame, viewW, viewH);
  const plotWProbe = Math.max(
    40,
    framedEarly
      ? viewW - framedEarly.left - framedEarly.right
      : viewW - baseMargin.left - baseMargin.right,
  );
  const plotHProbe = Math.max(
    40,
    framedEarly
      ? viewH - framedEarly.top - framedEarly.bottom
      : viewH - baseMargin.top - baseMargin.bottom,
  );
  /*
   * Categoria física: eixo X no vertical, eixo Y no horizontal_bar.
   * `visibleXLabelIndices` (nome legado) indexa categorias — não o eixo de valor.
   * Desligar só «Horizontal principal» (showX) não pode zerar categorias no Y.
   */
  const showXAxisLabels = Boolean(input.showXAxisLabels);
  const showYAxisLabels = input.showYAxisLabels !== false;
  const showCategoryLabels =
    orientation === "horizontal" ? showYAxisLabels : showXAxisLabels;
  const categoryAxisSpan = orientation === "horizontal" ? plotHProbe : plotWProbe;
  const skipDense = categoryLabelOverflow === "skip";
  const xLabelStep =
    showCategoryLabels && skipDense
      ? resolveXLabelStep(input.points.length, categoryAxisSpan, labels, axisFontSize)
      : 1;
  const autoRotate =
    orientation === "vertical" &&
    showCategoryLabels &&
    shouldRotateXLabels(input.points.length, xLabelStep, plotWProbe, labels, axisFontSize);
  const categoryLabelRotationDeg = resolveCategoryLabelRotationDeg(
    input.categoryLabelRotation,
    autoRotate,
  );
  const xLabelsRotated = categoryLabelRotationDeg !== 0;
  const visibleXLabelIndices = showCategoryLabels
    ? resolveVisibleXLabelIndices(input.points.length, xLabelStep)
    : [];

  const sides = resolveSideMargins(
    orientation === "vertical" && showCategoryLabels,
    labels,
    visibleXLabelIndices,
    baseMargin,
    axisFontSize,
  );
  const showYAxisTitle = Boolean(input.showYAxisTitle);
  const displayCategoryLabels = showCategoryLabels
    ? labels.map((label) =>
        resolveCategoryAxisLabelText(
          label,
          input.categoryLabelFormat,
          input.categoryLabelOverflow,
          input.displayCategoryFormat,
        ),
      )
    : labels;
  const categoryLabelLeftPad =
    orientation === "horizontal" && showCategoryLabels
      ? resolveHorizontalCategoryLabelLeftPad(displayCategoryLabels, axisFontSize)
      : 0;
  const valueTickLabels =
    orientation === "vertical" && showYAxisLabels
      ? ticks.map((tick) =>
          formatChartTick(
            tick,
            input.valueFormat ?? "auto",
            input.decimalPlaces,
            input.displayValueFormat,
          ),
        )
      : [];
  const valueAxisLeftPad =
    orientation === "vertical" && showYAxisLabels
      ? resolveValueAxisLabelLeftPad(valueTickLabels, axisFontSize)
      : 0;
  const leftLabelFloor = Math.max(categoryLabelLeftPad, valueAxisLeftPad);
  const cartesianAutoMargin: SeriesChartMargin = {
    top: baseMargin.top,
    left: Math.max(
      resolveLeftMarginWithYTitle(showYAxisTitle, sides.left, axisTitleFontSize),
      leftLabelFloor,
    ),
    right: Math.max(
      sides.right,
      hasSecondaryAxis ? Math.round(axisFontSize * 3.2) + 10 : sides.right,
      orientation === "horizontal" ? Math.round(axisFontSize * 2.2) : sides.right,
    ),
    bottom: resolveBottomMargin(
      orientation === "vertical" && showCategoryLabels,
      input.showXAxisTitle,
      xLabelsRotated,
      baseMargin,
      axisFontSize,
      axisTitleFontSize,
      categoryLabelRotationDeg,
    ),
  };
  const minLeftForYTitle = showYAxisTitle
    ? yAxisTitleGutterPx(axisTitleFontSize) + Math.round(axisFontSize * 2.6)
    : 0;
  const minLeftFloor = Math.max(minLeftForYTitle, leftLabelFloor);
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
          left: Math.max(framedEarly.left, minLeftFloor),
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
    {
      preferShrinkRight: orientation === "horizontal" && showCategoryLabels,
      preferShrinkTop: orientation === "vertical" && showCategoryLabels,
    },
  );

  const plotW = Math.max(1, viewW - margin.left - margin.right);
  const plotH = Math.max(1, viewH - margin.top - margin.bottom);
  const padPct = Math.max(0, Math.min(40, input.categoryPaddingPercent ?? 0));
  const markerGutter = Math.max(0, input.markerGutterPx ?? 0);
  // Cartesiano: inset 0 por padrão (extremos no eixo Y / borda direita).
  // Plot centralizado (pizza/funil) mantém folga mínima para não colar na moldura.
  const insetFromPercent =
    padPct > 0
      ? Math.round((plotW * padPct) / 100)
      : input.centeredPlot
        ? SERIES_CHART_PLOT_INSET
        : 0;
  const plotInset =
    Math.max(insetFromPercent, markerGutter) > 0
      ? Math.min(
          Math.floor(Math.min(plotW, plotH) / 6),
          Math.max(4, Math.max(insetFromPercent, markerGutter)),
        )
      : 0;
  const innerW = Math.max(1, plotW - 2 * plotInset);
  const insetGutter = Math.min(plotInset, Math.floor(plotH / 4));
  /**
   * Eixo de valor: folga no extremo alto (topo no vertical / direita no horizontal).
   * Base do eixo (min) permanece na borda do plot para área/barra alinharem ao eixo.
   */
  const valueHighGutter = input.centeredPlot
    ? insetGutter
    : Math.max(SERIES_CHART_VALUE_AXIS_GUTTER_PX, insetGutter);
  const valueLowGutter = insetGutter;
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
  const categoryInnerH = Math.max(1, plotH - 2 * insetGutter);
  const categoryBandHeight = (count: number) => {
    const n = Math.max(1, count);
    return categoryInnerH / n;
  };
  const categoryBandStartY = (index: number, count: number) => {
    const n = Math.max(1, count);
    const i = Math.min(Math.max(0, index), n - 1);
    return margin.top + insetGutter + (i / n) * categoryInnerH;
  };

  const valueInnerH = Math.max(1, plotH - valueHighGutter - valueLowGutter);
  const valueInnerW = Math.max(1, plotW - plotInset - Math.max(plotInset, valueHighGutter));

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
    return margin.top + valueHighGutter + (1 - t) * valueInnerH;
  };
  const toValueX = (value: number) => {
    const t = Math.min(1, Math.max(0, (value - axisMin) / axisRange));
    return margin.left + plotInset + t * valueInnerW;
  };
  const toYSecondary = hasSecondaryAxis
    ? (value: number) => {
        const t = Math.min(1, Math.max(0, (value - secondaryMin) / secondaryRange));
        return margin.top + valueHighGutter + (1 - t) * valueInnerH;
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
    orientation,
    ticks,
    axisMin,
    axisMax,
    axisRange,
    xLabelStep,
    xLabelsRotated,
    categoryLabelRotationDeg,
    categoryLabelOverflow,
    visibleXLabelIndices,
    toX,
    categoryBandStart,
    categoryBandWidth,
    toY,
    ...(orientation === "horizontal"
      ? { toValueX, categoryBandStartY, categoryBandHeight }
      : {}),
    ...(hasSecondaryAxis
      ? { toYSecondary, secondaryTicks, hasSecondaryAxis: true }
      : {}),
  };
}

export function resolveSeriesName(config: SeriesChartOptions): string {
  const title = config.title?.trim();
  return config.seriesName?.trim() || title || "Série";
}

export function formatChartTick(
  value: number,
  valueFormat: SeriesChartValueFormat,
  decimalPlaces?: number | null,
  spec?: DisplayFormatSpec | null,
): string {
  return formatSeriesChartValue(value, valueFormat, decimalPlaces, spec);
}

/** Aplica formato + overflow ao rótulo de categoria para paint. */
export function resolveCategoryAxisLabelText(
  raw: string,
  format: SeriesChartCategoryLabelFormat | undefined,
  overflow: SeriesChartCategoryLabelOverflow | undefined,
  spec?: DisplayFormatSpec | null,
): string {
  let text = formatSeriesChartCategoryLabel(raw, format ?? "raw", spec);
  if (overflow === "truncate") {
    text = truncateSeriesChartCategoryLabel(text);
  }
  return text;
}
