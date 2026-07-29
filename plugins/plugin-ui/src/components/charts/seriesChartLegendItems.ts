import {
  resolveSeriesChartLegendSort,
  type SeriesChartKind,
  type SeriesChartLegendSort,
  type SeriesChartLegendSortResolved,
  type SeriesChartPoint,
  type SeriesChartSeriesSpec,
} from "./seriesChartOptions";
import {
  resolveCategorySlicePaintColor,
  resolveSeriesPaintColor,
  type ChartPartsMap,
} from "./seriesChartParts";

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

function pointSortValue(point: SeriesChartPoint): number {
  const raw = point.value;
  if (raw === null || raw === undefined) return 0;
  const n = Number(raw);
  return Number.isFinite(n) ? n : 0;
}

function pointSortName(point: SeriesChartPoint): string {
  return point.label?.trim() || "";
}

export function sortSeriesChartPoints(
  points: SeriesChartPoint[],
  sort: SeriesChartLegendSortResolved,
): SeriesChartPoint[] {
  if (sort === "data" || points.length < 2) return points;
  const copy = [...points];
  if (sort === "valueDesc") {
    copy.sort((a, b) => pointSortValue(b) - pointSortValue(a));
  } else if (sort === "valueAsc") {
    copy.sort((a, b) => pointSortValue(a) - pointSortValue(b));
  } else if (sort === "nameAsc") {
    copy.sort((a, b) => pointSortName(a).localeCompare(pointSortName(b), "pt-BR"));
  } else if (sort === "nameDesc") {
    copy.sort((a, b) => pointSortName(b).localeCompare(pointSortName(a), "pt-BR"));
  }
  return copy;
}

function seriesSortTotal(series: SeriesChartSeriesSpec): number {
  return series.points.reduce((acc, point) => acc + pointSortValue(point), 0);
}

function seriesSortName(series: SeriesChartSeriesSpec, index: number): string {
  return series.name?.trim() || `Série ${index + 1}`;
}

export function sortSeriesChartSeriesList(
  seriesList: SeriesChartSeriesSpec[],
  sort: SeriesChartLegendSortResolved,
): SeriesChartSeriesSpec[] {
  if (sort === "data" || seriesList.length < 2) return seriesList;
  const indexed = seriesList.map((series, index) => ({ series, index }));
  if (sort === "valueDesc") {
    indexed.sort((a, b) => seriesSortTotal(b.series) - seriesSortTotal(a.series));
  } else if (sort === "valueAsc") {
    indexed.sort((a, b) => seriesSortTotal(a.series) - seriesSortTotal(b.series));
  } else if (sort === "nameAsc") {
    indexed.sort((a, b) =>
      seriesSortName(a.series, a.index).localeCompare(seriesSortName(b.series, b.index), "pt-BR"),
    );
  } else if (sort === "nameDesc") {
    indexed.sort((a, b) =>
      seriesSortName(b.series, b.index).localeCompare(seriesSortName(a.series, a.index), "pt-BR"),
    );
  }
  return indexed.map((entry) => entry.series);
}

/**
 * Aplica ordenação da legenda aos pontos de categoria (pizza/funil/empilhado).
 * Multi-série: a ordem das séries no plot permanece; só a lista da legenda
 * é reordenada em `buildSeriesChartLegendItems` (cores por índice original).
 */
export function applySeriesChartLegendSort(args: {
  chartType: SeriesChartKind;
  points: SeriesChartPoint[];
  seriesList?: SeriesChartSeriesSpec[] | null;
  sort?: SeriesChartLegendSort | null;
}): {
  points: SeriesChartPoint[];
  seriesList: SeriesChartSeriesSpec[] | null | undefined;
  resolvedSort: SeriesChartLegendSortResolved;
  usesCategoryLegend: boolean;
} {
  const { chartType, points, seriesList, sort } = args;
  const seriesWithData = seriesList?.filter((series) => series.points.length > 0);
  const seriesCount = seriesWithData?.length ?? 1;
  const usesCategoryLegend = seriesChartUsesCategoryLegend(chartType, seriesCount);
  const resolvedSort = resolveSeriesChartLegendSort({
    chartType,
    sort,
    usesCategoryLegend,
  });

  if (resolvedSort === "data" || !usesCategoryLegend) {
    return { points, seriesList, resolvedSort, usesCategoryLegend };
  }

  const sourcePoints = seriesWithData?.[0]?.points ?? points;
  const sortedPoints = sortSeriesChartPoints(sourcePoints, resolvedSort);
  if (seriesWithData?.[0]) {
    return {
      points: sortedPoints,
      seriesList: [{ ...seriesWithData[0], points: sortedPoints }],
      resolvedSort,
      usesCategoryLegend,
    };
  }
  return { points: sortedPoints, seriesList, resolvedSort, usesCategoryLegend };
}

function sortLegendItemsByMeta(
  items: Array<SeriesChartLegendItem & { sortValue: number; sortName: string }>,
  sort: SeriesChartLegendSortResolved,
): SeriesChartLegendItem[] {
  if (sort === "data" || items.length < 2) {
    return items.map(({ name, color }) => ({ name, color }));
  }
  const copy = [...items];
  if (sort === "valueDesc") {
    copy.sort((a, b) => b.sortValue - a.sortValue);
  } else if (sort === "valueAsc") {
    copy.sort((a, b) => a.sortValue - b.sortValue);
  } else if (sort === "nameAsc") {
    copy.sort((a, b) => a.sortName.localeCompare(b.sortName, "pt-BR"));
  } else if (sort === "nameDesc") {
    copy.sort((a, b) => b.sortName.localeCompare(a.sortName, "pt-BR"));
  }
  return copy.map(({ name, color }) => ({ name, color }));
}

/**
 * Entradas da legenda alinhadas ao encoding visual do gráfico.
 * - Multi-série → uma entrada por série.
 * - Pizza / funil / empilhado (série única) → uma entrada por categoria/fatia.
 * - Demais → `undefined` (fallback para `seriesName` + cor da série).
 *
 * Categorias devem chegar já ordenadas via `applySeriesChartLegendSort`.
 * Multi-série reordena só a legenda (plot mantém índices de cor).
 */
export function buildSeriesChartLegendItems(args: {
  chartType: SeriesChartKind;
  points: SeriesChartPoint[];
  seriesColor: string;
  seriesList?: SeriesChartSeriesSpec[] | null;
  categoryColors?: string[] | null;
  chartParts?: ChartPartsMap | null;
  sort?: SeriesChartLegendSort | null;
}): SeriesChartLegendItem[] | undefined {
  const { chartType, points, seriesColor, seriesList, categoryColors, chartParts, sort } = args;
  const seriesWithData = seriesList?.filter((series) => series.points.length > 0);
  const multiSeries = Boolean(seriesWithData && seriesWithData.length > 1);
  const seriesCount = seriesWithData?.length ?? 1;
  const usesCategoryLegend = seriesChartUsesCategoryLegend(chartType, seriesCount);
  const resolvedSort = resolveSeriesChartLegendSort({
    chartType,
    sort,
    usesCategoryLegend,
  });

  if (multiSeries && seriesWithData) {
    const items = seriesWithData.map((series, index) => ({
      name: series.name?.trim() || `Série ${index + 1}`,
      color: resolveSeriesPaintColor({
        seriesIndex: index,
        explicit: series.color,
        seriesColor,
        categoryColors,
        parts: chartParts,
      }),
      sortValue: seriesSortTotal(series),
      sortName: series.name?.trim() || `Série ${index + 1}`,
    }));
    return sortLegendItemsByMeta(items, resolvedSort);
  }

  if (!usesCategoryLegend) {
    return undefined;
  }

  const categoryPoints = seriesWithData?.[0]?.points ?? points;
  return categoryPoints.map((point, index) => ({
    name: point.label?.trim() || `Categoria ${index + 1}`,
    color: resolveCategorySlicePaintColor({
      index,
      sourceIndex: point.sourceIndex ?? index,
      seriesColor,
      categoryColors,
      parts: chartParts,
    }),
  }));
}
