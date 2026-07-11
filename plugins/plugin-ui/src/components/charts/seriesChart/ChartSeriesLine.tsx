import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  CHART_SERIES_LINE_STROKE_WIDTH,
  bindChartPartPointer,
  filterVisibleSeriesPoints,
  getChartPartState,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import type { SeriesChartSharedProps } from "./types";

export type ChartSeriesLineProps = Pick<SeriesChartSharedProps, "layout" | "points" | "seriesColor"> & {
  strokeWidth?: number;
  interaction?: SeriesChartInteraction | null;
  seriesIndex?: number;
  chartParts?: ChartPartsMap | null;
};

export function ChartSeriesLine({
  layout,
  points,
  seriesColor,
  strokeWidth = CHART_SERIES_LINE_STROKE_WIDTH,
  interaction,
  seriesIndex = 0,
  chartParts,
}: ChartSeriesLineProps) {
  const cn = useSeriesChartClasses();
  const { toX, toY } = layout;
  const ref = { kind: "series" as const, seriesIndex };
  const seriesVisible = getChartPartState(chartParts, ref)?.visible !== false;
  if (!seriesVisible) return null;

  const visiblePoints = filterVisibleSeriesPoints(points, chartParts, seriesIndex);
  if (visiblePoints.length === 0) return null;

  const { selected, onPointerDown, onDoubleClick, ...dom } = bindChartPartPointer(ref, interaction, {
    moveWhenSelected: false,
  });

  return (
    <polyline
      points={visiblePoints
        .map((point) => `${toX(point.sourceIndex, points.length)},${toY(Number(point.value))}`)
        .join(" ")}
      fill="none"
      stroke={seriesColor}
      strokeWidth={strokeWidth}
      vectorEffect="non-scaling-stroke"
      strokeLinejoin="round"
      strokeLinecap="round"
      className={[cn.seriesLine, selected ? `${cn.root}__part--selected` : ""].filter(Boolean).join(" ")}
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    />
  );
}
