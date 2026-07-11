/**
 * Onda 4G — partes endereçáveis do gráfico de série.
 * Uma fonte de verdade: identidade + adapter com `SeriesChartOptions` flat (legado v1.4).
 */

import type { PointerEvent as ReactPointerEvent } from "react";

import type { SeriesChartOptions } from "./seriesChartOptions";
import { mergeSeriesChartOptions } from "./seriesChartOptions";

/** Atributo DOM para hit-test no editor (sem HTML livre). */
export const CHART_PART_DATA_ATTR = "data-chart-part";

/**
 * Defaults alinhados a `ComunicadoVisualPrimitive` (point → line → area):
 * linha usa stroke; ponto usa fill + radius de hit.
 */
export const CHART_SERIES_LINE_STROKE_WIDTH = 2;
export const CHART_MARKER_RADIUS = 2.5;

export type ChartPartRef =
  | { kind: "title" }
  | { kind: "legend" }
  | { kind: "series"; seriesIndex: number }
  | { kind: "marker"; seriesIndex: number; pointIndex: number }
  | { kind: "dataLabel"; seriesIndex: number; pointIndex: number }
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
  /** Raio do marcador (primitivo point). */
  markerRadius?: number;
};

export type ChartPartState = {
  visible?: boolean;
  style?: ChartPartStyle;
  /** Título, axisTitle, seriesName, etc. */
  content?: string;
};

export type ChartPartsMap = Record<string, ChartPartState>;

export type SeriesChartInteraction = {
  selectedPart?: ChartPartRef | null;
  onPartPointerDown?: (ref: ChartPartRef, event: ReactPointerEvent) => void;
};

export function serializeChartPartRef(ref: ChartPartRef): string {
  switch (ref.kind) {
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
  if (value === "title") return { kind: "title" };
  if (value === "legend") return { kind: "legend" };
  if (value === "grid") return { kind: "grid" };
  if (value === "dataTable") return { kind: "dataTable" };

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

export function chartPartDomProps(
  ref: ChartPartRef,
  selectedPart?: ChartPartRef | null,
): { [CHART_PART_DATA_ATTR]: string; "aria-selected": boolean } {
  return {
    [CHART_PART_DATA_ATTR]: serializeChartPartRef(ref),
    "aria-selected": isChartPartRefEqual(ref, selectedPart),
  };
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

export function upsertChartPartState(
  parts: ChartPartsMap | null | undefined,
  ref: ChartPartRef,
  patch: ChartPartState,
): ChartPartsMap {
  const key = serializeChartPartRef(ref);
  const prev = parts?.[key] ?? {};
  return {
    ...(parts ?? {}),
    [key]: {
      ...prev,
      ...patch,
      style: patch.style ? { ...prev.style, ...patch.style } : prev.style,
    },
  };
}

/** Projeta options flat → partes (visibilidade + conteúdo + cor da série). */
export function chartOptionsToParts(options?: SeriesChartOptions | null): ChartPartsMap {
  const config = mergeSeriesChartOptions(options);
  const parts: ChartPartsMap = {};

  parts[serializeChartPartRef({ kind: "title" })] = {
    visible: config.showTitle !== false,
    content: config.title?.trim() || undefined,
  };

  parts[serializeChartPartRef({ kind: "legend" })] = {
    visible: config.showLegend !== false && config.legendPosition !== "hidden",
    content: config.seriesName?.trim() || undefined,
  };

  parts[serializeChartPartRef({ kind: "series", seriesIndex: 0 })] = {
    visible: true,
    content: config.seriesName?.trim() || undefined,
    style: {
      stroke: config.seriesColor,
      strokeWidth: CHART_SERIES_LINE_STROKE_WIDTH,
      fill: config.seriesColor,
    },
  };

  parts[serializeChartPartRef({ kind: "axis", axis: "x" })] = {
    visible: config.showAxes !== false && config.showXAxisLabels !== false,
  };
  parts[serializeChartPartRef({ kind: "axis", axis: "y" })] = {
    visible: config.showAxes !== false && config.showYAxisLabels !== false,
  };
  parts[serializeChartPartRef({ kind: "axisTitle", axis: "x" })] = {
    visible: config.showXAxisTitle === true,
    content: config.xAxisTitle?.trim() || undefined,
  };
  parts[serializeChartPartRef({ kind: "axisTitle", axis: "y" })] = {
    visible: config.showYAxisTitle === true,
    content: config.yAxisTitle?.trim() || undefined,
  };
  parts[serializeChartPartRef({ kind: "grid" })] = {
    visible: config.showGrid !== false || Boolean(config.showVerticalGrid),
  };
  parts[serializeChartPartRef({ kind: "dataTable" })] = {
    visible: Boolean(config.showDataTable),
  };

  return parts;
}

/** Partes → options flat (compat v1.4 / inspector legado). */
export function partsToChartOptions(parts?: ChartPartsMap | null): Partial<SeriesChartOptions> {
  if (!parts) return {};

  const title = getChartPartState(parts, { kind: "title" });
  const legend = getChartPartState(parts, { kind: "legend" });
  const series = getChartPartState(parts, { kind: "series", seriesIndex: 0 });
  const axisX = getChartPartState(parts, { kind: "axis", axis: "x" });
  const axisY = getChartPartState(parts, { kind: "axis", axis: "y" });
  const axisTitleX = getChartPartState(parts, { kind: "axisTitle", axis: "x" });
  const axisTitleY = getChartPartState(parts, { kind: "axisTitle", axis: "y" });
  const grid = getChartPartState(parts, { kind: "grid" });
  const dataTable = getChartPartState(parts, { kind: "dataTable" });

  const patch: Partial<SeriesChartOptions> = {};

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
  if (grid?.visible !== undefined) {
    patch.showGrid = grid.visible;
    patch.showVerticalGrid = grid.visible;
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
  const fromParts = partsToChartOptions(parts);
  return mergeSeriesChartOptions({ ...mergeSeriesChartOptions(options), ...fromParts });
}

/** Cor da série: primitivo line (stroke) com fallback options. */
export function resolveSeriesStrokeColor(
  options: SeriesChartOptions,
  parts?: ChartPartsMap | null,
): string {
  const series = getChartPartState(parts, { kind: "series", seriesIndex: 0 });
  return series?.style?.stroke ?? series?.style?.fill ?? options.seriesColor ?? "#0d7a8c";
}

export function resolveSeriesStrokeWidth(parts?: ChartPartsMap | null): number {
  const series = getChartPartState(parts, { kind: "series", seriesIndex: 0 });
  return series?.style?.strokeWidth ?? CHART_SERIES_LINE_STROKE_WIDTH;
}

export function resolveMarkerStyle(
  parts: ChartPartsMap | null | undefined,
  seriesIndex: number,
  pointIndex: number,
  seriesColor: string,
): { fill: string; stroke?: string; radius: number; visible: boolean } {
  const marker = getChartPartState(parts, { kind: "marker", seriesIndex, pointIndex });
  const series = getChartPartState(parts, { kind: "series", seriesIndex });
  const fill = marker?.style?.fill ?? series?.style?.fill ?? seriesColor;
  const stroke = marker?.style?.stroke;
  const radius = marker?.style?.markerRadius ?? CHART_MARKER_RADIUS;
  const visible = marker?.visible !== false;
  return { fill, stroke, radius, visible };
}
