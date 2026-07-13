export type {
  SeriesChartValueFormat as ComunicadoChartValueFormat,
  SeriesChartLegendPosition as ComunicadoChartLegendPosition,
  SeriesChartOptions as ComunicadoChartOptions,
  SeriesChartPoint,
  SeriesChartKind,
} from "@delpi/plugin-ui/index";

export {
  DEFAULT_SERIES_CHART_OPTIONS as DEFAULT_COMUNICADO_CHART_OPTIONS,
  OFFICE_CHART_AREA_FILL,
  OFFICE_CHART_AREA_STROKE,
  OFFICE_CHART_PLOT_FILL,
  OFFICE_CHART_PLOT_STROKE,
  OFFICE_CHART_SERIES_COLOR,
  SERIES_CHART_VALUE_FORMAT_OPTIONS as CHART_VALUE_FORMAT_OPTIONS,
  SERIES_CHART_LEGEND_POSITION_OPTIONS as CHART_LEGEND_POSITION_OPTIONS,
  formatSeriesChartValue,
  mergeSeriesChartOptions as mergeComunicadoChartOptions,
  migrateSeriesChartOptionsOnLoad as migrateComunicadoChartOptionsOnLoad,
  resolveSeriesChartDisplayOptions as resolveChartDisplayOptions,
  resolveSeriesChartTicks,
  usableSeriesChartPoints,
} from "@delpi/plugin-ui/index";
