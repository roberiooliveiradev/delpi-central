/**
 * Reexport canônico das partes do gráfico (Onda 4G) — sem duplicar lógica.
 */
export type {
  ChartPartRef as ComunicadoChartPartRef,
  ChartPartState as ComunicadoChartPartState,
  ChartPartStyle as ComunicadoChartPartStyle,
  ChartPartsMap as ComunicadoChartPartsMap,
  SeriesChartInteraction as ComunicadoChartInteraction,
} from "@delpi/plugin-ui/index";

export {
  CHART_MARKER_RADIUS,
  CHART_PART_DATA_ATTR,
  CHART_SERIES_LINE_STROKE_WIDTH,
  chartOptionsToParts,
  chartPartDomProps,
  findChartPartFromTarget,
  getChartPartState,
  isChartPartRefEqual,
  mergeSeriesChartOptionsWithParts,
  parseChartPartRef,
  partsToChartOptions,
  resolveMarkerStyle,
  resolveSeriesStrokeColor,
  resolveSeriesStrokeWidth,
  serializeChartPartRef,
  upsertChartPartState,
} from "@delpi/plugin-ui/index";
