/** Janela deslizante sobre pontos de série temporal (gráficos longos). */

export type ChartSeriesWindowState<T> = {
  visible: T[];
  navigable: boolean;
  offset: number;
  maxOffset: number;
  total: number;
  windowSize: number;
  page: number;
  pageCount: number;
  rangeLabel: string;
};

export const DEFAULT_CHART_SERIES_WINDOW_SIZE = 24;

function formatRangeLabel<T extends { name?: string }>(points: T[]): string {
  if (points.length === 0) return "";
  if (points.length === 1) return String(points[0]?.name ?? "");
  const first = points[0]?.name ?? "";
  const last = points[points.length - 1]?.name ?? "";
  return `${first} — ${last}`;
}

export function getChartSeriesWindow<T extends { name?: string; sortKey?: string }>(
  points: T[],
  offset: number,
  windowSize: number = DEFAULT_CHART_SERIES_WINDOW_SIZE,
): ChartSeriesWindowState<T> {
  const total = points.length;
  if (total === 0) {
    return {
      visible: [],
      navigable: false,
      offset: 0,
      maxOffset: 0,
      total: 0,
      windowSize,
      page: 0,
      pageCount: 0,
      rangeLabel: "",
    };
  }

  if (total <= windowSize) {
    return {
      visible: points,
      navigable: false,
      offset: 0,
      maxOffset: 0,
      total,
      windowSize,
      page: 1,
      pageCount: 1,
      rangeLabel: formatRangeLabel(points),
    };
  }

  const maxOffset = total - windowSize;
  const clampedOffset = Math.max(0, Math.min(offset, maxOffset));
  const visible = points.slice(clampedOffset, clampedOffset + windowSize);
  const page = Math.floor(clampedOffset / windowSize) + 1;
  const pageCount = Math.ceil(total / windowSize);

  return {
    visible,
    navigable: true,
    offset: clampedOffset,
    maxOffset,
    total,
    windowSize,
    page,
    pageCount,
    rangeLabel: formatRangeLabel(visible),
  };
}

export function clampChartOffset(offset: number, total: number, windowSize: number): number {
  if (total <= windowSize) return 0;
  return Math.max(0, Math.min(offset, total - windowSize));
}
