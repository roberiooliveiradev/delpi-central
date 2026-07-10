import type { SeriesChartOptions, SeriesChartKind } from "./seriesChartOptions";

export type SeriesChartElementId =
  | "axes"
  | "axisTitles"
  | "chartTitle"
  | "dataLabels"
  | "dataTable"
  | "gridlines"
  | "legend"
  | "markers";

export type SeriesChartElementDefinition = {
  id: SeriesChartElementId;
  label: string;
  hint?: string;
  chartTypes?: SeriesChartKind[];
};

export const SERIES_CHART_ELEMENT_CATALOG: SeriesChartElementDefinition[] = [
  { id: "axes", label: "Eixos", hint: "Linhas dos eixos e rótulos de escala." },
  { id: "axisTitles", label: "Títulos dos eixos", hint: "Nome descritivo dos eixos X e Y." },
  { id: "chartTitle", label: "Título do gráfico", hint: "Título central acima da área de plotagem." },
  { id: "dataLabels", label: "Rótulos de dados", hint: "Valor exibido em cada ponto ou barra." },
  { id: "dataTable", label: "Tabela de dados", hint: "Grade com períodos e valores abaixo do gráfico." },
  { id: "gridlines", label: "Linhas de grade", hint: "Linhas horizontais e verticais de referência." },
  { id: "legend", label: "Legenda", hint: "Identificação da série de dados." },
  { id: "markers", label: "Marcadores", hint: "Pontos sobre a linha do gráfico.", chartTypes: ["line"] },
];

export function isSeriesChartElementApplicable(
  element: SeriesChartElementDefinition,
  chartType: SeriesChartKind,
): boolean {
  return !element.chartTypes || element.chartTypes.includes(chartType);
}

export function isSeriesChartElementEnabled(
  elementId: SeriesChartElementId,
  options: SeriesChartOptions,
): boolean {
  switch (elementId) {
    case "axes":
      return options.showAxes !== false;
    case "axisTitles":
      return options.showXAxisTitle === true || options.showYAxisTitle === true;
    case "chartTitle":
      return options.showTitle !== false;
    case "dataLabels":
      return Boolean(options.showDataLabels);
    case "dataTable":
      return Boolean(options.showDataTable);
    case "gridlines":
      return options.showGrid !== false || Boolean(options.showVerticalGrid);
    case "legend":
      return options.showLegend !== false && options.legendPosition !== "hidden";
    case "markers":
      return options.showMarkers !== false;
    default:
      return false;
  }
}

export function setSeriesChartElementEnabled(
  elementId: SeriesChartElementId,
  enabled: boolean,
): Partial<SeriesChartOptions> {
  switch (elementId) {
    case "axes":
      return {
        showAxes: enabled,
        showXAxisLabels: enabled,
        showYAxisLabels: enabled,
      };
    case "axisTitles":
      return {
        showXAxisTitle: enabled,
        showYAxisTitle: enabled,
      };
    case "chartTitle":
      return { showTitle: enabled };
    case "dataLabels":
      return { showDataLabels: enabled };
    case "dataTable":
      return { showDataTable: enabled };
    case "gridlines":
      return { showGrid: enabled, showVerticalGrid: enabled };
    case "legend":
      return enabled
        ? { showLegend: true, legendPosition: "bottom" }
        : { showLegend: false, legendPosition: "hidden" };
    case "markers":
      return { showMarkers: enabled };
    default:
      return {};
  }
}

export const CHART_ELEMENT_CATALOG = SERIES_CHART_ELEMENT_CATALOG;
export const isChartElementApplicable = isSeriesChartElementApplicable;
export const isChartElementEnabled = isSeriesChartElementEnabled;
export const setChartElementEnabled = setSeriesChartElementEnabled;

export type ChartElementId = SeriesChartElementId;
export type ChartElementDefinition = SeriesChartElementDefinition;
