import type { ComunicadoChartOptions } from "./comunicadoChartOptions";
import type { SeriesChartKind } from "./comunicadoChartOptions";

export type ChartElementId =
  | "axes"
  | "axisTitles"
  | "chartTitle"
  | "dataLabels"
  | "dataTable"
  | "gridlines"
  | "legend"
  | "markers";

export type ChartElementDefinition = {
  id: ChartElementId;
  label: string;
  hint?: string;
  /** Tipos de gráfico em que o elemento se aplica; omitido = todos. */
  chartTypes?: SeriesChartKind[];
};

/** Catálogo alinhado ao menu «Adicionar elemento de gráfico» do Excel. */
export const CHART_ELEMENT_CATALOG: ChartElementDefinition[] = [
  { id: "axes", label: "Eixos", hint: "Linhas dos eixos e rótulos de escala." },
  { id: "axisTitles", label: "Títulos dos eixos", hint: "Nome descritivo dos eixos X e Y." },
  { id: "chartTitle", label: "Título do gráfico", hint: "Título central acima da área de plotagem." },
  { id: "dataLabels", label: "Rótulos de dados", hint: "Valor exibido em cada ponto ou barra." },
  { id: "dataTable", label: "Tabela de dados", hint: "Grade com períodos e valores abaixo do gráfico." },
  { id: "gridlines", label: "Linhas de grade", hint: "Linhas horizontais e verticais de referência." },
  { id: "legend", label: "Legenda", hint: "Identificação da série de dados." },
  { id: "markers", label: "Marcadores", hint: "Pontos sobre a linha do gráfico.", chartTypes: ["line"] },
];

export function isChartElementApplicable(
  element: ChartElementDefinition,
  chartType: SeriesChartKind,
): boolean {
  return !element.chartTypes || element.chartTypes.includes(chartType);
}

export function isChartElementEnabled(
  elementId: ChartElementId,
  options: ComunicadoChartOptions,
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

export function setChartElementEnabled(
  elementId: ChartElementId,
  enabled: boolean,
): Partial<ComunicadoChartOptions> {
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
