/**
 * Onda 4G — partes endereçáveis do gráfico de série.
 * Uma fonte de verdade: identidade + adapter com `SeriesChartOptions` flat (legado v1.4).
 */

import type {
  CSSProperties,
  MouseEvent as ReactMouseEvent,
  PointerEvent as ReactPointerEvent,
} from "react";

import type { SeriesChartOptions } from "./seriesChartOptions";
import {
  mergeSeriesChartOptions,
  OFFICE_CHART_AREA_FILL,
  OFFICE_CHART_AREA_STROKE,
  OFFICE_CHART_PLOT_FILL,
  OFFICE_CHART_PLOT_STROKE,
  OFFICE_CHART_SERIES_COLOR,
  type SeriesChartKind,
} from "./seriesChartOptions";
import { DECK_CHART_DEFAULTS } from "../../theme/deckColorCatalog";
import { resolveTextPartColumnBoxLayout } from "../../utils/textPartBoxLayout";

/** Atributo DOM para hit-test no editor (sem HTML livre). */
export const CHART_PART_DATA_ATTR = "data-chart-part";

/**
 * Defaults alinhados a `ComunicadoVisualPrimitive` (point → line → area):
 * linha usa stroke; ponto usa fill + radius.
 * Unidades SVG do gráfico (não % do palco de formas).
 */
export type ChartVisualPrimitive = "point" | "line" | "area";

/** Espessura semântica da linha (igual `defaultStrokeWidthForPrimitive("line")`). */
export const CHART_LINE_STROKE_WIDTH_SEMANTIC = 4;
/** Espessura renderizada no SVG (escala do viewBox). */
export const CHART_SERIES_LINE_STROKE_WIDTH = 2;
/** Raio do marcador no SVG (primitivo point). */
export const CHART_MARKER_RADIUS = 2.5;

export function chartPartVisualPrimitive(
  ref: ChartPartRef,
  chartType?: SeriesChartKind,
): ChartVisualPrimitive | null {
  switch (ref.kind) {
    case "series":
      if (
        chartType === "area" ||
        chartType === "pie" ||
        chartType === "bar" ||
        chartType === "stacked_bar" ||
        chartType === "histogram" ||
        chartType === "waterfall" ||
        chartType === "funnel" ||
        chartType === "radar" ||
        chartType === "bubble"
      ) {
        return "area";
      }
      if (chartType === "combo") return "line";
      if (chartType === "scatter") return "point";
      return "line";
    case "marker":
      return chartType === "pie" || chartType === "funnel" ? "area" : "point";
    case "grid":
    case "axes":
    case "axis":
      return "line";
    case "chartArea":
    case "plotArea":
      return "area";
    default:
      return null;
  }
}

export function defaultStrokeWidthForChartPrimitive(primitive: ChartVisualPrimitive): number {
  if (primitive === "point") return 0;
  if (primitive === "line") return CHART_SERIES_LINE_STROKE_WIDTH;
  return CHART_SERIES_LINE_STROKE_WIDTH;
}

export function chartPrimitiveSupportsFill(primitive: ChartVisualPrimitive): boolean {
  return primitive !== "line";
}

export function chartPrimitiveSupportsStroke(primitive: ChartVisualPrimitive): boolean {
  return primitive === "line" || primitive === "area" || primitive === "point";
}

export type ChartPartRef =
  | { kind: "chartArea" }
  | { kind: "plotArea" }
  | { kind: "title" }
  | { kind: "legend" }
  | { kind: "series"; seriesIndex: number }
  | { kind: "marker"; seriesIndex: number; pointIndex: number }
  | { kind: "dataLabel"; seriesIndex: number; pointIndex: number }
  /** Seleção em lote — tipografia comum a todos os rótulos de dados. */
  | { kind: "dataLabels" }
  /** Seleção em lote — eixos X+Y (contorno/highlight). */
  | { kind: "axes" }
  | { kind: "axis"; axis: "x" | "y" }
  | { kind: "axisTitle"; axis: "x" | "y" }
  | { kind: "grid" }
  | { kind: "dataTable" };

/** Subconjunto de estilo herdável de forma/texto — sem reinventar no chart. */
export type ChartPartStyle = {
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
  opacity?: number;
  fontFamily?: string;
  fontSize?: number;
  color?: string;
  fontWeight?: "normal" | "bold";
  fontStyle?: "normal" | "italic";
  textAlign?: "left" | "center" | "right" | "justify";
  verticalAlign?: "top" | "middle" | "bottom";
  /** Raio do marcador (primitivo point). */
  markerRadius?: number;
  /** Cantos (Format Shape) — padrão visual Delpi = DECK_CHART_DEFAULTS.borderRadius. */
  borderRadius?: number;
  /** Sombra do box (CSS box-shadow) — tipicamente na parte `chartArea`. */
  boxShadow?: string;
  /** Sombra tipográfica (título/legenda). */
  textShadow?: string;
  textStrokeColor?: string;
  textStrokeWidth?: number;
  textReflection?: boolean;
};

export type ChartPartFrame = {
  x: number;
  y: number;
  w?: number;
  h?: number;
};

export type ChartPartState = {
  visible?: boolean;
  style?: ChartPartStyle;
  /** Título, axisTitle, seriesName, etc. */
  content?: string;
  /**
   * Posição % relativa ao bloco chart (title / legend / dataTable)
   * ou ao host do SVG (`plotArea`, 4H.6).
   */
  frame?: ChartPartFrame;
};

export type ChartPartStatePatch = Omit<ChartPartState, "frame" | "style"> & {
  style?: Partial<ChartPartStyle>;
  /** `null` remove o frame. */
  frame?: ChartPartFrame | null;
};

export type ChartPartsMap = Record<string, ChartPartState>;

export type SeriesChartInteraction = {
  selectedPart?: ChartPartRef | null;
  /** Parte em edição inline (ex.: título). */
  editingPart?: ChartPartRef | null;
  onPartPointerDown?: (ref: ChartPartRef, event: ReactPointerEvent) => void;
  onPartDoubleClick?: (ref: ChartPartRef, event: ReactPointerEvent | ReactMouseEvent) => void;
  onPartContentCommit?: (ref: ChartPartRef, content: string) => void;
  onPartEditCancel?: () => void;
  /** Inicia arraste de parte móvel (title/legend). */
  onPartMovePointerDown?: (ref: ChartPartRef, event: ReactPointerEvent) => void;
  /** Inicia resize de parte com frame (title/legend/dataTable). */
  onPartResizePointerDown?: (
    ref: ChartPartRef,
    event: ReactPointerEvent,
    handle: ChartPartResizeHandle,
  ) => void;
  /** Materializa frame % medido no DOM (seleção sem frame prévio). */
  onPartFrameChange?: (ref: ChartPartRef, frame: ChartPartFrame) => void;
};

export type ChartPartResizeHandle = "nw" | "n" | "ne" | "e" | "se" | "s" | "sw" | "w";

export const CHART_PART_RESIZE_HANDLES: ChartPartResizeHandle[] = [
  "nw",
  "n",
  "ne",
  "e",
  "se",
  "s",
  "sw",
  "w",
];

export function serializeChartPartRef(ref: ChartPartRef): string {
  switch (ref.kind) {
    case "chartArea":
      return "chartArea";
    case "plotArea":
      return "plotArea";
    case "title":
      return "title";
    case "legend":
      return "legend";
    case "grid":
      return "grid";
    case "dataTable":
      return "dataTable";
    case "series":
      return `series:${ref.seriesIndex}`;
    case "marker":
      return `marker:${ref.seriesIndex}:${ref.pointIndex}`;
    case "dataLabel":
      return `dataLabel:${ref.seriesIndex}:${ref.pointIndex}`;
    case "dataLabels":
      return "dataLabels";
    case "axes":
      return "axes";
    case "axis":
      return `axis:${ref.axis}`;
    case "axisTitle":
      return `axisTitle:${ref.axis}`;
    default: {
      const _exhaustive: never = ref;
      return String(_exhaustive);
    }
  }
}

export function parseChartPartRef(raw: string | null | undefined): ChartPartRef | null {
  const value = (raw ?? "").trim();
  if (!value) return null;
  if (value === "chartArea") return { kind: "chartArea" };
  if (value === "plotArea") return { kind: "plotArea" };
  if (value === "title") return { kind: "title" };
  if (value === "legend") return { kind: "legend" };
  if (value === "grid") return { kind: "grid" };
  if (value === "dataTable") return { kind: "dataTable" };
  if (value === "dataLabels") return { kind: "dataLabels" };
  if (value === "axes") return { kind: "axes" };

  const series = /^series:(\d+)$/.exec(value);
  if (series) return { kind: "series", seriesIndex: Number(series[1]) };

  const marker = /^marker:(\d+):(\d+)$/.exec(value);
  if (marker) {
    return {
      kind: "marker",
      seriesIndex: Number(marker[1]),
      pointIndex: Number(marker[2]),
    };
  }

  const dataLabel = /^dataLabel:(\d+):(\d+)$/.exec(value);
  if (dataLabel) {
    return {
      kind: "dataLabel",
      seriesIndex: Number(dataLabel[1]),
      pointIndex: Number(dataLabel[2]),
    };
  }

  const axis = /^axis:(x|y)$/.exec(value);
  if (axis) return { kind: "axis", axis: axis[1] as "x" | "y" };

  const axisTitle = /^axisTitle:(x|y)$/.exec(value);
  if (axisTitle) return { kind: "axisTitle", axis: axisTitle[1] as "x" | "y" };

  return null;
}

export function isChartPartRefEqual(a: ChartPartRef | null | undefined, b: ChartPartRef | null | undefined): boolean {
  if (!a || !b) return a === b;
  return serializeChartPartRef(a) === serializeChartPartRef(b);
}

/** Seleção visual: grupos `dataLabels` / `axes` destacam partes individuais. */
export function isChartPartInteractionSelected(
  ref: ChartPartRef,
  selectedPart?: ChartPartRef | null,
): boolean {
  if (!selectedPart) return false;
  if (selectedPart.kind === "dataLabels" && ref.kind === "dataLabel") return true;
  if (selectedPart.kind === "axes" && ref.kind === "axis") return true;
  return isChartPartRefEqual(ref, selectedPart);
}

export function chartPartDomProps(
  ref: ChartPartRef,
  selectedPart?: ChartPartRef | null,
): { [CHART_PART_DATA_ATTR]: string; "aria-selected": boolean } {
  return {
    [CHART_PART_DATA_ATTR]: serializeChartPartRef(ref),
    "aria-selected": isChartPartInteractionSelected(ref, selectedPart),
  };
}

/** Capacidades declarativas por kind (Excel Format Object). */
export type ChartPartCapabilities = {
  movable: boolean;
  editable: boolean;
  deletable: boolean;
  /** Handles de redimensionamento (title / legend / dataTable com frame). */
  resizable: boolean;
};

const CHART_PART_KIND_CAPABILITIES: Record<ChartPartRef["kind"], ChartPartCapabilities> = {
  chartArea: { movable: true, editable: false, deletable: false, resizable: true },
  plotArea: { movable: true, editable: false, deletable: false, resizable: true },
  title: { movable: true, editable: true, deletable: true, resizable: true },
  legend: { movable: true, editable: true, deletable: true, resizable: true },
  series: { movable: false, editable: false, deletable: true, resizable: false },
  marker: { movable: false, editable: false, deletable: true, resizable: false },
  dataLabel: { movable: false, editable: true, deletable: true, resizable: false },
  dataLabels: { movable: false, editable: true, deletable: true, resizable: false },
  /** Eixos ganham/perdem espaço via `plotArea.frame` (4H.6) — sem frame próprio. */
  axes: { movable: false, editable: false, deletable: true, resizable: false },
  axis: { movable: false, editable: false, deletable: true, resizable: false },
  axisTitle: { movable: false, editable: true, deletable: true, resizable: false },
  grid: { movable: false, editable: false, deletable: true, resizable: false },
  dataTable: { movable: false, editable: false, deletable: true, resizable: false },
};

export function chartPartCapabilities(ref: ChartPartRef): ChartPartCapabilities {
  return CHART_PART_KIND_CAPABILITIES[ref.kind];
}

export type BindChartPartPointerOptions = {
  /**
   * Inicia arraste só com a parte já selecionada (default: true quando movable).
   * Passar `false` para desligar move neste host.
   */
  moveWhenSelected?: boolean;
  /** Força estado de edição inline (title contentEditable). */
  editing?: boolean;
};

/**
 * Hit-test unificado: data-attr + pointer/double-click (+ move se selecionada).
 * Substitui boilerplate repetido em ChartTitle / Legend / Axis / …
 */
export function bindChartPartPointer(
  ref: ChartPartRef,
  interaction?: SeriesChartInteraction | null,
  opts?: BindChartPartPointerOptions,
) {
  const interactive = Boolean(interaction?.onPartPointerDown || interaction?.onPartDoubleClick);
  const selected = isChartPartInteractionSelected(ref, interaction?.selectedPart);
  const editing = opts?.editing ?? isChartPartRefEqual(ref, interaction?.editingPart);
  const caps = chartPartCapabilities(ref);
  const moveWhenSelected = opts?.moveWhenSelected !== false && caps.movable;
  const dom = chartPartDomProps(ref, interaction?.selectedPart);

  if (!interactive) {
    return {
      ...dom,
      selected,
      editing,
      onPointerDown: undefined as undefined,
      onDoubleClick: undefined as undefined,
    };
  }

  return {
    ...dom,
    selected,
    editing,
    onPointerDown: (event: ReactPointerEvent) => {
      if (editing) {
        event.stopPropagation();
        return;
      }
      event.stopPropagation();
      interaction?.onPartPointerDown?.(ref, event);
      if (moveWhenSelected && selected) {
        interaction?.onPartMovePointerDown?.(ref, event);
      }
    },
    onDoubleClick: (event: ReactMouseEvent) => {
      event.stopPropagation();
      event.preventDefault();
      interaction?.onPartDoubleClick?.(ref, event);
    },
  };
}

/**
 * Normaliza parts no load: garante projeção options→parts e desliga moldura
 * legada do plot (`strokeWidth: 1` era o default antigo que vazava eixos).
 * Remove frame da dataTable (sempre no fluxo) e plotArea com geometria inválida.
 */
export function normalizeChartPartsForLoad(
  parts: ChartPartsMap | null | undefined,
  options?: SeriesChartOptions | null,
): ChartPartsMap {
  const merged = mergeChartPartsWithOptions(parts, options);
  const plotKey = serializeChartPartRef({ kind: "plotArea" });
  const plot = merged[plotKey];
  if (plot?.style?.strokeWidth === 1) {
    merged[plotKey] = {
      ...plot,
      style: { ...plot.style, strokeWidth: 0 },
    };
  }
  const plotAfter = merged[plotKey];
  if (plotAfter?.frame && !isUsablePlotFrame(plotAfter.frame)) {
    const { frame: _drop, ...rest } = plotAfter;
    merged[plotKey] = rest;
  }
  const tableKey = serializeChartPartRef({ kind: "dataTable" });
  const table = merged[tableKey];
  if (table?.frame) {
    const { frame: _dropTableFrame, ...tableRest } = table;
    merged[tableKey] = tableRest;
  }
  return merged;
}

/** Frame do plot precisa de área útil; senão o SVG some (w/h ~0). */
function isUsablePlotFrame(frame: ChartPartFrame): boolean {
  return (
    frame.w != null &&
    frame.h != null &&
    Number.isFinite(frame.w) &&
    Number.isFinite(frame.h) &&
    frame.w >= 15 &&
    frame.h >= 15
  );
}

export function findChartPartFromTarget(target: EventTarget | null): ChartPartRef | null {
  if (!(target instanceof Element)) return null;
  const host = target.closest(`[${CHART_PART_DATA_ATTR}]`);
  if (!host) return null;
  return parseChartPartRef(host.getAttribute(CHART_PART_DATA_ATTR));
}

export function getChartPartState(parts: ChartPartsMap | null | undefined, ref: ChartPartRef): ChartPartState | undefined {
  if (!parts) return undefined;
  return parts[serializeChartPartRef(ref)];
}

/** Tipografia padrão das partes textuais — alinhada ao CSS do gráfico (não ao 16 fantasma da ribbon). */
export const CHART_PART_FONT_SIZE_DEFAULTS = {
  title: 14,
  legend: 10,
  axis: 9,
  axisTitle: 9,
  dataLabel: 8,
  dataLabels: 8,
} as const;

export type ChartTextPartKind = keyof typeof CHART_PART_FONT_SIZE_DEFAULTS;

export function isChartTextPartKind(kind: string): kind is ChartTextPartKind {
  return kind in CHART_PART_FONT_SIZE_DEFAULTS;
}

/**
 * Tamanho efetivo da parte — mesma regra do KPI (`resolveKpiPartFontSize`).
 * Ribbon e render devem consumir isto; nunca um default genérico 16.
 */
export function resolveChartPartFontSize(
  kind: ChartTextPartKind,
  style?: { fontSize?: number } | null,
): number {
  const explicit = style?.fontSize;
  if (explicit != null && Number.isFinite(explicit) && explicit > 0) {
    return Math.round(explicit);
  }
  return CHART_PART_FONT_SIZE_DEFAULTS[kind];
}

/** Tipografia declarada em chartParts — sempre emite fontSize canônico (paridade DelpiKpiCard). */
export function chartPartTypographyStyle(
  parts: ChartPartsMap | null | undefined,
  ref: ChartPartRef,
  options?: { boxLayout?: boolean },
): CSSProperties | undefined {
  const pointStyle = getChartPartState(parts, ref)?.style;
  const groupStyle =
    ref.kind === "dataLabel"
      ? getChartPartState(parts, { kind: "dataLabels" })?.style
      : undefined;
  const style = groupStyle || pointStyle ? { ...groupStyle, ...pointStyle } : undefined;
  const css: CSSProperties = {};
  const textKind =
    ref.kind === "dataLabels"
      ? "dataLabels"
      : isChartTextPartKind(ref.kind)
        ? ref.kind
        : null;
  if (textKind) {
    css.fontSize = `${resolveChartPartFontSize(textKind, style)}px`;
  }
  if (!style) {
    return Object.keys(css).length > 0 ? css : undefined;
  }
  if (style.fontFamily) css.fontFamily = style.fontFamily;
  if (style.fontWeight) css.fontWeight = style.fontWeight;
  if (style.fontStyle) css.fontStyle = style.fontStyle;
  if (style.color) {
    css.color = style.color;
    /* SVG `<text>` usa `fill`; `color` sozinho não pinta o eixo. */
    css.fill = style.color;
  }
  const useBoxLayout =
    options?.boxLayout === true ||
    ref.kind === "title" ||
    Boolean(style.verticalAlign) ||
    Boolean(style.textAlign);
  if (useBoxLayout && (ref.kind === "title" || options?.boxLayout)) {
    Object.assign(
      css,
      resolveTextPartColumnBoxLayout({
        textAlign: style.textAlign,
        verticalAlign: style.verticalAlign,
        defaultVerticalAlign: "top",
        fillHost: true,
      }),
    );
  } else if (style.textAlign) {
    css.textAlign = style.textAlign;
  }
  return Object.keys(css).length > 0 ? css : undefined;
}

export function upsertChartPartState(
  parts: ChartPartsMap | null | undefined,
  ref: ChartPartRef,
  patch: ChartPartStatePatch,
): ChartPartsMap {
  const key = serializeChartPartRef(ref);
  const prev = parts?.[key] ?? {};
  const nextFrame =
    patch.frame === null
      ? undefined
      : patch.frame !== undefined
        ? clampChartPartFrame({ ...(prev.frame ?? {}), ...patch.frame })
        : prev.frame;
  const { frame: _ignored, ...restPatch } = patch;
  return {
    ...(parts ?? {}),
    [key]: {
      ...prev,
      ...restPatch,
      style: patch.style ? { ...prev.style, ...patch.style } : prev.style,
      frame: nextFrame,
    },
  };
}

/** Projeta options flat → partes (visibilidade + conteúdo + cor da série). */
export function chartOptionsToParts(options?: SeriesChartOptions | null): ChartPartsMap {
  const config = mergeSeriesChartOptions(options);
  const parts: ChartPartsMap = {};

  parts[serializeChartPartRef({ kind: "chartArea" })] = {
    visible: true,
    style: {
      fill: config.backgroundColor ?? DECK_CHART_DEFAULTS.areaFill,
      stroke: DECK_CHART_DEFAULTS.areaStroke,
      strokeWidth: DECK_CHART_DEFAULTS.borderWidth,
      borderRadius: DECK_CHART_DEFAULTS.borderRadius,
      boxShadow: DECK_CHART_DEFAULTS.boxShadow,
    },
  };

  parts[serializeChartPartRef({ kind: "plotArea" })] = {
    visible: true,
    style: {
      fill: DECK_CHART_DEFAULTS.plotFill,
      stroke: DECK_CHART_DEFAULTS.plotStroke,
      // Contorno do plot desligado por default — eixos já delimitam (evita moldura dupla).
      strokeWidth: 0,
      borderRadius: 0,
    },
  };

  parts[serializeChartPartRef({ kind: "title" })] = {
    visible: config.showTitle !== false,
    content: config.title?.trim() || undefined,
  };

  parts[serializeChartPartRef({ kind: "legend" })] = {
    visible: config.showLegend !== false && config.legendPosition !== "hidden",
    content: config.seriesName?.trim() || undefined,
  };

  const seriesFill =
    config.categoryColors?.[1]?.trim() || config.seriesColor;
  parts[serializeChartPartRef({ kind: "series", seriesIndex: 0 })] = {
    visible: true,
    content: config.seriesName?.trim() || undefined,
    style: {
      stroke: config.seriesColor,
      strokeWidth: CHART_SERIES_LINE_STROKE_WIDTH,
      fill: seriesFill,
    },
  };

  parts[serializeChartPartRef({ kind: "axes" })] = {
    visible: config.showAxes !== false,
  };
  parts[serializeChartPartRef({ kind: "axis", axis: "x" })] = {
    visible: config.showAxes !== false && config.showXAxisLabels !== false,
  };
  parts[serializeChartPartRef({ kind: "axis", axis: "y" })] = {
    visible: config.showAxes !== false && config.showYAxisLabels !== false,
  };
  parts[serializeChartPartRef({ kind: "axisTitle", axis: "x" })] = {
    visible: config.showXAxisTitle !== false,
    content: config.xAxisTitle?.trim() || undefined,
  };
  parts[serializeChartPartRef({ kind: "axisTitle", axis: "y" })] = {
    visible: config.showYAxisTitle !== false,
    content: config.yAxisTitle?.trim() || undefined,
  };
  parts[serializeChartPartRef({ kind: "grid" })] = {
    visible: config.showGrid !== false || Boolean(config.showVerticalGrid),
  };
  parts[serializeChartPartRef({ kind: "dataTable" })] = {
    visible: Boolean(config.showDataTable),
  };
  parts[serializeChartPartRef({ kind: "dataLabels" })] = {
    visible: Boolean(config.showDataLabels),
  };

  return parts;
}

/**
 * Projeta options → parts preservando estilos custom (área/bordas/marcadores).
 * Usar no inspetor em vez de `chartOptionsToParts` puro.
 */
export function mergeChartPartsWithOptions(
  parts: ChartPartsMap | null | undefined,
  options?: SeriesChartOptions | null,
): ChartPartsMap {
  const projected = chartOptionsToParts(options);
  const prev = parts ?? {};
  const merged: ChartPartsMap = { ...projected };

  for (const key of Object.keys(prev)) {
    const prevState = prev[key];
    const projectedState = projected[key];
    if (!prevState) continue;
    if (key === "chartArea" || key === "plotArea" || key === "dataLabels" || key.startsWith("dataLabel:")) {
      merged[key] = {
        ...projectedState,
        ...prevState,
        style: {
          ...projectedState?.style,
          ...prevState.style,
          ...(key === "chartArea" && projectedState?.style?.fill
            ? { fill: projectedState.style.fill }
            : {}),
        },
      };
    } else if (key.startsWith("marker:")) {
      const showMarkers = options?.showMarkers !== false;
      merged[key] = {
        ...projectedState,
        ...prevState,
        /* Estilo «Com marcadores» / showMarkers flat manda na visibilidade. */
        visible: showMarkers,
        style: {
          ...projectedState?.style,
          ...prevState.style,
        },
      };
    } else if (key.startsWith("series:")) {
      /* seriesColor flat (Alterar cores / inspetor) regrava stroke+fill; demais estilos custom ficam. */
      merged[key] = {
        ...projectedState,
        ...prevState,
        visible: projectedState?.visible ?? prevState.visible,
        style: {
          ...projectedState?.style,
          ...prevState.style,
          ...(projectedState?.style?.stroke
            ? {
                stroke: projectedState.style.stroke,
                fill: projectedState.style.fill ?? projectedState.style.stroke,
              }
            : {}),
        },
        content:
          projectedState?.content !== undefined ? projectedState.content : prevState.content,
        frame: prevState.frame ?? projectedState?.frame,
      };
    } else if (prevState.style || prevState.frame || prevState.content !== undefined) {
      const preserveFrame = !key.startsWith("dataTable");
      merged[key] = {
        ...projectedState,
        ...prevState,
        visible: projectedState?.visible ?? prevState.visible,
        style: { ...projectedState?.style, ...prevState.style },
        frame: preserveFrame ? (prevState.frame ?? projectedState?.frame) : undefined,
      };
    }
  }

  return merged;
}

/** Partes → options flat (compat v1.4 / inspector legado). */
export function partsToChartOptions(parts?: ChartPartsMap | null): Partial<SeriesChartOptions> {
  if (!parts) return {};

  const title = getChartPartState(parts, { kind: "title" });
  const legend = getChartPartState(parts, { kind: "legend" });
  const series = getChartPartState(parts, { kind: "series", seriesIndex: 0 });
  const chartArea = getChartPartState(parts, { kind: "chartArea" });
  const axisX = getChartPartState(parts, { kind: "axis", axis: "x" });
  const axisY = getChartPartState(parts, { kind: "axis", axis: "y" });
  const axisTitleX = getChartPartState(parts, { kind: "axisTitle", axis: "x" });
  const axisTitleY = getChartPartState(parts, { kind: "axisTitle", axis: "y" });
  const grid = getChartPartState(parts, { kind: "grid" });
  const dataTable = getChartPartState(parts, { kind: "dataTable" });

  const patch: Partial<SeriesChartOptions> = {};

  if (chartArea?.style?.fill) {
    patch.backgroundColor = chartArea.style.fill;
    /* theme vive só nas options flat — nunca forçar light aqui (quebra Estilo Escuro). */
  }

  if (axisX?.visible === false && axisY?.visible === false) {
    patch.showAxes = false;
  } else if (axisX?.visible === true || axisY?.visible === true) {
    patch.showAxes = true;
  }

  if (title) {
    if (title.visible !== undefined) patch.showTitle = title.visible;
    if (title.content !== undefined) patch.title = title.content;
  }
  if (legend) {
    if (legend.visible === false) {
      patch.showLegend = false;
      patch.legendPosition = "hidden";
    } else if (legend.visible === true) {
      patch.showLegend = true;
      if (patch.legendPosition === "hidden") patch.legendPosition = "bottom";
    }
    if (legend.content !== undefined) patch.seriesName = legend.content;
  }
  if (series) {
    if (series.content !== undefined) patch.seriesName = series.content;
    const color = series.style?.stroke ?? series.style?.fill;
    if (color) patch.seriesColor = color;
  }
  if (axisX?.visible !== undefined) patch.showXAxisLabels = axisX.visible;
  if (axisY?.visible !== undefined) patch.showYAxisLabels = axisY.visible;
  if (axisTitleX) {
    if (axisTitleX.visible !== undefined) patch.showXAxisTitle = axisTitleX.visible;
    if (axisTitleX.content !== undefined) patch.xAxisTitle = axisTitleX.content;
  }
  if (axisTitleY) {
    if (axisTitleY.visible !== undefined) patch.showYAxisTitle = axisTitleY.visible;
    if (axisTitleY.content !== undefined) patch.yAxisTitle = axisTitleY.content;
  }
  /*
   * Grade: `visible:false` desliga H+V. `visible:true` não força vertical —
   * H/V independentes vivem nas options flat (inspetor / Adicionar elemento).
   * Forçar showVerticalGrid = visible quebrava o round-trip e “apagava” alterações.
   */
  if (grid?.visible === false) {
    patch.showGrid = false;
    patch.showVerticalGrid = false;
  }
  if (dataTable?.visible !== undefined) patch.showDataTable = dataTable.visible;

  const anyMarkerHidden = Object.keys(parts).some((key) => {
    const ref = parseChartPartRef(key);
    return ref?.kind === "marker" && parts[key]?.visible === false;
  });
  const anyMarkerShown = Object.keys(parts).some((key) => {
    const ref = parseChartPartRef(key);
    return ref?.kind === "marker" && parts[key]?.visible === true;
  });
  if (anyMarkerHidden && !anyMarkerShown) patch.showMarkers = false;

  return patch;
}

/**
 * Resolve options efetivas: base flat + override de `chartParts`.
 * Único ponto de merge para render (admin + TV).
 */
export function mergeSeriesChartOptionsWithParts(
  options?: SeriesChartOptions | null,
  parts?: ChartPartsMap | null,
): SeriesChartOptions {
  const base = mergeSeriesChartOptions(options);
  const fromParts = { ...partsToChartOptions(parts) };
  /* Seed legado gravava axisTitle visible:false sem texto — não apagar show ligado nas options. */
  const axisTitleX = getChartPartState(parts, { kind: "axisTitle", axis: "x" });
  const axisTitleY = getChartPartState(parts, { kind: "axisTitle", axis: "y" });
  if (
    base.showXAxisTitle !== false &&
    fromParts.showXAxisTitle === false &&
    !String(axisTitleX?.content ?? "").trim()
  ) {
    delete fromParts.showXAxisTitle;
  }
  if (
    base.showYAxisTitle !== false &&
    fromParts.showYAxisTitle === false &&
    !String(axisTitleY?.content ?? "").trim()
  ) {
    delete fromParts.showYAxisTitle;
  }
  return mergeSeriesChartOptions({ ...base, ...fromParts });
}

/** Cor da série: primitivo line (stroke) — única fonte; `seriesColor` só como fallback legado. */
/**
 * Traço efetivo de linha (eixo / grade): herda estilo do grupo (`axes`) quando houver.
 * ChartGrid / ChartAxisLines consomem — chrome de contorno não pode ser no-op.
 */
export function resolveChartLinePartStroke(
  parts: ChartPartsMap | null | undefined,
  ref: ChartPartRef,
): { stroke?: string; strokeWidth?: number; opacity?: number } {
  const own = getChartPartState(parts, ref)?.style;
  const group =
    ref.kind === "axis" ? getChartPartState(parts, { kind: "axes" })?.style : undefined;
  const style = group || own ? { ...group, ...own } : undefined;
  if (!style) return {};
  return {
    stroke: style.stroke,
    strokeWidth: style.strokeWidth,
    opacity: style.opacity,
  };
}

export function resolveSeriesStrokeColor(
  options: SeriesChartOptions,
  parts?: ChartPartsMap | null,
): string {
  const series = getChartPartState(parts, { kind: "series", seriesIndex: 0 });
  return series?.style?.stroke ?? series?.style?.fill ?? options.seriesColor ?? OFFICE_CHART_SERIES_COLOR;
}

export function resolveSeriesStrokeWidth(parts?: ChartPartsMap | null): number {
  const series = getChartPartState(parts, { kind: "series", seriesIndex: 0 });
  const primitive = "line" as const;
  return series?.style?.strokeWidth ?? defaultStrokeWidthForChartPrimitive(primitive);
}

/**
 * Marcador (point): fill herda stroke da série; stroke/radius opcionais no part.
 */
export function resolveMarkerStyle(
  parts: ChartPartsMap | null | undefined,
  seriesIndex: number,
  pointIndex: number,
  seriesColor: string,
): { fill: string; stroke?: string; strokeWidth: number; radius: number; visible: boolean } {
  const marker = getChartPartState(parts, { kind: "marker", seriesIndex, pointIndex });
  const series = getChartPartState(parts, { kind: "series", seriesIndex });
  const inheritedFill = series?.style?.stroke ?? series?.style?.fill ?? seriesColor;
  const fill = marker?.style?.fill ?? inheritedFill;
  const stroke = marker?.style?.stroke;
  const strokeWidth =
    marker?.style?.strokeWidth ?? defaultStrokeWidthForChartPrimitive("point");
  const radius = marker?.style?.markerRadius ?? CHART_MARKER_RADIUS;
  const visible = marker?.visible !== false;
  return { fill, stroke, strokeWidth, radius, visible };
}

/** Estilo efetivo da série como primitivo `line`. */
export function resolveSeriesLineStyle(
  options: SeriesChartOptions,
  parts?: ChartPartsMap | null,
): { stroke: string; strokeWidth: number; opacity?: number } {
  const series = getChartPartState(parts, { kind: "series", seriesIndex: 0 });
  return {
    stroke: resolveSeriesStrokeColor(options, parts),
    strokeWidth: resolveSeriesStrokeWidth(parts),
    opacity: series?.style?.opacity,
  };
}

export function chartPartAllowsMove(ref: ChartPartRef): boolean {
  return chartPartCapabilities(ref).movable;
}

export function chartPartAllowsDelete(ref: ChartPartRef): boolean {
  return chartPartCapabilities(ref).deletable;
}

export function chartPartAllowsEdit(ref: ChartPartRef): boolean {
  return chartPartCapabilities(ref).editable;
}

export function chartPartAllowsResize(ref: ChartPartRef): boolean {
  return chartPartCapabilities(ref).resizable;
}

/** Partes com geometria % editável (title / legend / plotArea). */
export function chartPartAllowsFrame(ref: ChartPartRef): boolean {
  return chartPartAllowsMove(ref) || chartPartAllowsResize(ref);
}

/** Frame % padrão ao abrir inspetor/ribbon antes da materialização no DOM. */
export function defaultChartPartFrame(ref: ChartPartRef): ChartPartFrame {
  switch (ref.kind) {
    case "title":
      return { x: 10, y: 2, w: 80, h: 10 };
    case "legend":
      return { x: 10, y: 85, w: 80, h: 10 };
    case "plotArea":
      return { x: 8, y: 8, w: 84, h: 84 };
    case "chartArea":
      return { x: 0, y: 0, w: 100, h: 100 };
    default:
      return { x: 10, y: 10, w: 40, h: 20 };
  }
}

/**
 * Raiz de geometria para move/resize de `frame`.
 * `chartArea` = bloco do gráfico; `plotArea` = host do SVG; demais = raiz do gráfico.
 */
export function resolveChartPartFrameRoot(
  ref: ChartPartRef,
  from: Element,
): Element | null {
  if (ref.kind === "chartArea") {
    return (
      from.closest(".tdp-comunicado__block--chart-view, .td-composer__chart-view") ??
      from.parentElement
    );
  }
  if (ref.kind === "plotArea") {
    return from.closest(".delpi-ui-series-chart__plot-host, .tdp-series-chart__plot-host");
  }
  return from.closest(".delpi-ui-series-chart, .tdp-series-chart");
}

/** Aplica delta % de resize no frame da parte (igual handles do bloco). */
export function resizeChartPartFrame(
  frame: ChartPartFrame,
  handle: ChartPartResizeHandle,
  dx: number,
  dy: number,
): ChartPartFrame {
  let x = frame.x;
  let y = frame.y;
  let w = frame.w ?? 20;
  let h = frame.h ?? 8;
  switch (handle) {
    case "se":
      w += dx;
      h += dy;
      break;
    case "e":
      w += dx;
      break;
    case "s":
      h += dy;
      break;
    case "n":
      y += dy;
      h -= dy;
      break;
    case "w":
      x += dx;
      w -= dx;
      break;
    case "ne":
      y += dy;
      h -= dy;
      w += dx;
      break;
    case "nw":
      x += dx;
      y += dy;
      w -= dx;
      h -= dy;
      break;
    case "sw":
      x += dx;
      w -= dx;
      h += dy;
      break;
    default: {
      const _exhaustive: never = handle;
      return _exhaustive;
    }
  }
  return clampChartPartFrame({ x, y, w, h });
}

export function clampChartPartFrame(frame: ChartPartFrame): ChartPartFrame {
  const x = Math.max(0, Math.min(95, frame.x));
  const y = Math.max(0, Math.min(95, frame.y));
  const w = frame.w == null ? undefined : Math.max(5, Math.min(100 - x, frame.w));
  const h = frame.h == null ? undefined : Math.max(5, Math.min(100 - y, frame.h));
  return { x, y, w, h };
}

/** Oculta parte (Delete Excel) e projeta options flat — não remove o bloco chart. */
export function deleteChartPart(
  parts: ChartPartsMap | null | undefined,
  ref: ChartPartRef,
  options?: SeriesChartOptions | null,
): { parts: ChartPartsMap; options: SeriesChartOptions } {
  if (!chartPartAllowsDelete(ref)) {
    return {
      parts: parts ?? {},
      options: mergeSeriesChartOptions(options),
    };
  }
  const nextParts = upsertChartPartState(parts, ref, { visible: false });
  const fromParts = partsToChartOptions(nextParts);
  const base = mergeSeriesChartOptions({ ...options, ...fromParts });
  if (ref.kind === "series") {
    base.showMarkers = false;
  }
  return { parts: nextParts, options: base };
}

/** Aplica estilo de marcador a todos os pontos (Excel: Format Data Point → Apply to All). */
export function applyMarkerStyleToAll(
  parts: ChartPartsMap | null | undefined,
  pointCount: number,
  seriesIndex: number,
  style: ChartPartStyle,
): ChartPartsMap {
  let next = parts ?? {};
  const count = Math.max(0, pointCount);
  for (let pointIndex = 0; pointIndex < count; pointIndex += 1) {
    next = upsertChartPartState(next, { kind: "marker", seriesIndex, pointIndex }, { style });
  }
  return next;
}

/**
 * Pontos efetivos para desenhar a série: remove índices com marker visible:false.
 * Índices originais preservados via `sourceIndex` para hit-test.
 */
export function filterVisibleSeriesPoints<T extends { value?: number | null }>(
  points: T[],
  parts: ChartPartsMap | null | undefined,
  seriesIndex = 0,
): Array<T & { sourceIndex: number }> {
  return points
    .map((point, sourceIndex) => ({ ...point, sourceIndex }))
    .filter((point) => {
      const marker = getChartPartState(parts, {
        kind: "marker",
        seriesIndex,
        pointIndex: point.sourceIndex,
      });
      return marker?.visible !== false;
    });
}

export function nudgeChartPartFrame(
  parts: ChartPartsMap | null | undefined,
  ref: ChartPartRef,
  dx: number,
  dy: number,
): ChartPartsMap {
  if (!chartPartAllowsMove(ref)) return parts ?? {};
  const current = getChartPartState(parts, ref)?.frame ?? { x: 50, y: ref.kind === "title" ? 2 : 85 };
  const next = clampChartPartFrame({
    ...current,
    x: current.x + dx,
    y: current.y + dy,
  });
  return upsertChartPartState(parts, ref, { frame: next });
}

/** Format Chart Area (Excel) — preenchimento + contorno + cantos + sombra. */
export function resolveChartAreaStyle(
  options: SeriesChartOptions,
  parts?: ChartPartsMap | null,
): {
  fill: string;
  stroke: string;
  strokeWidth: number;
  borderRadius: number;
  boxShadow: string;
} {
  const area = getChartPartState(parts, { kind: "chartArea" });
  const style = area?.style;
  /* Legado: sem `borderRadius`/`boxShadow` explícitos → chrome Delpi.
   * `borderRadius: 0` é válido (cantos retos) e NÃO dispara o fallback. */
  const hasExplicitRadius = typeof style?.borderRadius === "number";
  const hasExplicitShadow = Boolean(style?.boxShadow?.trim());
  const legacyOfficeChrome = !hasExplicitRadius && !hasExplicitShadow;
  return {
    fill: style?.fill ?? options.backgroundColor ?? DECK_CHART_DEFAULTS.areaFill,
    stroke: style?.stroke ?? DECK_CHART_DEFAULTS.areaStroke,
    strokeWidth: style?.strokeWidth ?? DECK_CHART_DEFAULTS.borderWidth,
    borderRadius: hasExplicitRadius
      ? Math.max(0, style!.borderRadius!)
      : DECK_CHART_DEFAULTS.borderRadius,
    boxShadow: hasExplicitShadow
      ? style!.boxShadow!
      : legacyOfficeChrome
        ? DECK_CHART_DEFAULTS.boxShadow
        : (style?.boxShadow ?? DECK_CHART_DEFAULTS.boxShadow),
  };
}

/** Format Plot Area (Excel). */
export function resolvePlotAreaStyle(parts?: ChartPartsMap | null): {
  fill: string;
  stroke: string;
  strokeWidth: number;
  borderRadius: number;
} {
  const area = getChartPartState(parts, { kind: "plotArea" });
  return {
    fill: area?.style?.fill ?? OFFICE_CHART_PLOT_FILL,
    stroke: area?.style?.stroke ?? OFFICE_CHART_PLOT_STROKE,
    strokeWidth: area?.style?.strokeWidth ?? 0,
    borderRadius: area?.style?.borderRadius ?? 0,
  };
}
