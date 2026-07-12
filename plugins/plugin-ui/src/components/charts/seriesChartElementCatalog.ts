import type { SeriesChartOptions, SeriesChartKind } from "./seriesChartOptions";
import { mergeSeriesChartOptions } from "./seriesChartOptions";
import {
  chartOptionsToParts,
  serializeChartPartRef,
  upsertChartPartState,
  type ChartPartRef,
  type ChartPartsMap,
} from "./seriesChartParts";

export type SeriesChartElementId =
  | "chartArea"
  | "plotArea"
  | "axes"
  | "axisTitles"
  | "chartTitle"
  | "dataLabels"
  | "dataTable"
  | "gridlines"
  | "legend"
  | "markers"
  | "series";

export type SeriesChartElementDefinition = {
  id: SeriesChartElementId;
  label: string;
  hint?: string;
  chartTypes?: SeriesChartKind[];
};

export const SERIES_CHART_ELEMENT_CATALOG: SeriesChartElementDefinition[] = [
  { id: "chartArea", label: "Área do gráfico", hint: "Fundo e borda externa do gráfico." },
  { id: "plotArea", label: "Área de plotagem", hint: "Fundo e borda da área onde a série é desenhada." },
  { id: "chartTitle", label: "Título do gráfico", hint: "Título central acima da área de plotagem." },
  { id: "series", label: "Série", hint: "Linha, colunas, área ou fatias dos dados." },
  { id: "legend", label: "Legenda", hint: "Identificação da série de dados." },
  {
    id: "axes",
    label: "Eixos",
    hint: "Linhas dos eixos e rótulos de escala.",
    chartTypes: ["line", "bar", "area", "combo"],
  },
  {
    id: "axisTitles",
    label: "Títulos dos eixos",
    hint: "Nome descritivo dos eixos X e Y.",
    chartTypes: ["line", "bar", "area", "combo"],
  },
  {
    id: "gridlines",
    label: "Linhas de grade",
    hint: "Linhas horizontais e verticais de referência.",
    chartTypes: ["line", "bar", "area", "combo"],
  },
  { id: "markers", label: "Marcadores", hint: "Pontos sobre a linha do gráfico.", chartTypes: ["line", "area", "combo"] },
  { id: "dataLabels", label: "Rótulos de dados", hint: "Valor exibido em cada ponto ou barra." },
  { id: "dataTable", label: "Tabela de dados", hint: "Grade com períodos e valores abaixo do gráfico." },
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
    case "chartArea":
    case "plotArea":
    case "series":
      return true;
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
    case "chartArea":
    case "plotArea":
    case "series":
      return {};
    default:
      return {};
  }
}

/** Partes endereçáveis cobertas pelo item do catálogo (Onda 4G.7). */
export function chartElementPartRefs(elementId: SeriesChartElementId): ChartPartRef[] {
  switch (elementId) {
    case "chartArea":
      return [{ kind: "chartArea" }];
    case "plotArea":
      return [{ kind: "plotArea" }];
    case "chartTitle":
      return [{ kind: "title" }];
    case "legend":
      return [{ kind: "legend" }];
    case "series":
      return [{ kind: "series", seriesIndex: 0 }];
    case "axes":
      return [
        { kind: "axis", axis: "x" },
        { kind: "axis", axis: "y" },
      ];
    case "axisTitles":
      return [
        { kind: "axisTitle", axis: "x" },
        { kind: "axisTitle", axis: "y" },
      ];
    case "gridlines":
      return [{ kind: "grid" }];
    case "dataTable":
      return [{ kind: "dataTable" }];
    case "markers":
      return [{ kind: "marker", seriesIndex: 0, pointIndex: 0 }];
    case "dataLabels":
      return [{ kind: "dataLabel", seriesIndex: 0, pointIndex: 0 }];
    default:
      return [];
  }
}

/** Parte principal para seleção no palco ao focar o item do catálogo. */
export function chartElementPrimaryPartRef(elementId: SeriesChartElementId): ChartPartRef | null {
  return chartElementPartRefs(elementId)[0] ?? null;
}

/**
 * Liga/desliga elemento sincronizando `chartOptions` flat e `chartParts`.
 * Fonte canônica para o inspetor (sem duplicar toggles só em options).
 */
export function applyChartElementVisibility(
  elementId: SeriesChartElementId,
  enabled: boolean,
  options: SeriesChartOptions,
  parts?: ChartPartsMap | null,
): { options: SeriesChartOptions; parts: ChartPartsMap } {
  const optionPatch = setSeriesChartElementEnabled(elementId, enabled);
  const nextOptions = mergeSeriesChartOptions({ ...options, ...optionPatch });
  let nextParts: ChartPartsMap = { ...(parts ?? {}), ...chartOptionsToParts(options) };

  for (const ref of chartElementPartRefs(elementId)) {
    nextParts = upsertChartPartState(nextParts, ref, { visible: enabled });
  }

  nextParts = { ...nextParts, ...chartOptionsToParts(nextOptions) };
  return { options: nextOptions, parts: nextParts };
}

export function chartElementIdForPartRef(ref: ChartPartRef): SeriesChartElementId | null {
  switch (ref.kind) {
    case "title":
      return "chartTitle";
    case "legend":
      return "legend";
    case "series":
      return "series";
    case "axis":
      return "axes";
    case "axisTitle":
      return "axisTitles";
    case "grid":
      return "gridlines";
    case "dataTable":
      return "dataTable";
    case "marker":
      return "markers";
    case "dataLabel":
      return "dataLabels";
    default:
      return null;
  }
}

export function isChartElementOpenForPart(
  elementId: SeriesChartElementId,
  selectedPart: ChartPartRef | null | undefined,
): boolean {
  if (!selectedPart) return false;
  return chartElementIdForPartRef(selectedPart) === elementId;
}

/** @deprecated prefer serializeChartPartRef */
export function chartPartKey(ref: ChartPartRef): string {
  return serializeChartPartRef(ref);
}

export const CHART_ELEMENT_CATALOG = SERIES_CHART_ELEMENT_CATALOG;
export const isChartElementApplicable = isSeriesChartElementApplicable;
export const isChartElementEnabled = isSeriesChartElementEnabled;
export const setChartElementEnabled = setSeriesChartElementEnabled;

export type ChartElementId = SeriesChartElementId;
export type ChartElementDefinition = SeriesChartElementDefinition;
