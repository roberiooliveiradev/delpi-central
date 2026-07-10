export type {
  SeriesChartValueFormat as ComunicadoChartValueFormat,
  SeriesChartLegendPosition as ComunicadoChartLegendPosition,
  SeriesChartOptions as ComunicadoChartOptions,
  SeriesChartPoint,
  SeriesChartKind,
} from "@delpi/plugin-ui/index";

export {
  DEFAULT_SERIES_CHART_OPTIONS as DEFAULT_COMUNICADO_CHART_OPTIONS,
  SERIES_CHART_VALUE_FORMAT_OPTIONS as CHART_VALUE_FORMAT_OPTIONS,
  SERIES_CHART_LEGEND_POSITION_OPTIONS as CHART_LEGEND_POSITION_OPTIONS,
  formatSeriesChartValue,
  mergeSeriesChartOptions as mergeComunicadoChartOptions,
  resolveSeriesChartDisplayOptions as resolveChartDisplayOptions,
  resolveSeriesChartTicks,
  usableSeriesChartPoints,
} from "@delpi/plugin-ui/index";
