import { MAX_PERIOD_BUCKETS } from "./periodBuckets";

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

export function getChartSeriesWindow<T extends { name?: string; sortKey?: string }>(
  points: T[],
  offset: number,
  windowSize: number = MAX_PERIOD_BUCKETS
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

function formatRangeLabel<T extends { name?: string }>(points: T[]): string {
  if (points.length === 0) return "";
  if (points.length === 1) return String(points[0].name ?? "");
  return `${points[0].name ?? ""} — ${points[points.length - 1].name ?? ""}`;
}

export function clampChartOffset(offset: number, total: number, windowSize: number): number {
  if (total <= windowSize) return 0;
  return Math.max(0, Math.min(offset, total - windowSize));
}
