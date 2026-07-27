import {
  SERIES_CHART_CATEGORY_PALETTE,
  resolveSeriesCategoryColor,
  type SeriesChartKind,
  type SeriesChartPoint,
  type SeriesChartSeriesSpec,
} from "./seriesChartOptions";

export type SeriesChartLegendItem = {
  name: string;
  color: string;
};

/**
 * Tipos em que cada ponto é uma fatia/segmento com cor própria —
 * a legenda deve listar categorias, não o nome da série.
 */
const CATEGORY_LEGEND_KINDS: ReadonlySet<SeriesChartKind> = new Set([
  "pie",
  "funnel",
  "stacked_bar",
]);

export function seriesChartUsesCategoryLegend(
  chartType: SeriesChartKind,
  seriesCount: number,
): boolean {
  if (seriesCount > 1) return false;
  return CATEGORY_LEGEND_KINDS.has(chartType);
}

/**
 * Entradas da legenda alinhadas ao encoding visual do gráfico.
 * - Multi-série → uma entrada por série.
 * - Pizza / funil / empilhado (série única) → uma entrada por categoria/fatia.
 * - Demais → `undefined` (fallback para `seriesName` + cor da série).
 */
export function buildSeriesChartLegendItems(args: {
  chartType: SeriesChartKind;
  points: SeriesChartPoint[];
  seriesColor: string;
  seriesList?: SeriesChartSeriesSpec[] | null;
  categoryColors?: string[] | null;
}): SeriesChartLegendItem[] | undefined {
  const { chartType, points, seriesColor, seriesList, categoryColors } = args;
  const seriesWithData = seriesList?.filter((series) => series.points.length > 0);
  const multiSeries = Boolean(seriesWithData && seriesWithData.length > 1);

  if (multiSeries && seriesWithData) {
    return seriesWithData.map((series, index) => ({
      name: series.name?.trim() || `Série ${index + 1}`,
      color:
        series.color?.trim() ||
        categoryColors?.[index] ||
        SERIES_CHART_CATEGORY_PALETTE[index % SERIES_CHART_CATEGORY_PALETTE.length] ||
        seriesColor,
    }));
  }

  const seriesCount = seriesWithData?.length ?? 1;
  if (!seriesChartUsesCategoryLegend(chartType, seriesCount)) {
    return undefined;
  }

  const categoryPoints = seriesWithData?.[0]?.points ?? points;
  return categoryPoints.map((point, index) => ({
    name: point.label?.trim() || `Categoria ${index + 1}`,
    color: resolveSeriesCategoryColor(index, seriesColor, categoryColors),
  }));
}
