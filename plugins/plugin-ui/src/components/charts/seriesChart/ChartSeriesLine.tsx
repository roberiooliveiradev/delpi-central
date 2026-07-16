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
  strokeDasharray?: string;
  plotOn?: "primary" | "secondary";
  interaction?: SeriesChartInteraction | null;
  seriesIndex?: number;
  chartParts?: ChartPartsMap | null;
};

export function ChartSeriesLine({
  layout,
  points,
  seriesColor,
  strokeWidth = CHART_SERIES_LINE_STROKE_WIDTH,
  strokeDasharray,
  plotOn = "primary",
  interaction,
  seriesIndex = 0,
  chartParts,
}: ChartSeriesLineProps) {
  const cn = useSeriesChartClasses();
  const { toX, toY, toYSecondary } = layout;
  const mapY =
    plotOn === "secondary" && toYSecondary ? toYSecondary : toY;
  const ref = { kind: "series" as const, seriesIndex };
  const partStyle = getChartPartState(chartParts, ref)?.style;
  const seriesVisible = getChartPartState(chartParts, ref)?.visible !== false;
  if (!seriesVisible) return null;

  const visiblePoints = filterVisibleSeriesPoints(points, chartParts, seriesIndex);
  if (visiblePoints.length === 0) return null;

  const effectiveWidth = partStyle?.strokeWidth ?? strokeWidth;
  const effectiveDash = partStyle?.strokeDasharray?.trim() || strokeDasharray;

  const { selected, onPointerDown, onDoubleClick, ...dom } = bindChartPartPointer(ref, interaction, {
    moveWhenSelected: false,
  });

  return (
    <polyline
      points={visiblePoints
        .map((point) => `${toX(point.sourceIndex, points.length)},${mapY(Number(point.value))}`)
        .join(" ")}
      fill="none"
      stroke={seriesColor}
      strokeWidth={effectiveWidth}
      {...(effectiveDash ? { strokeDasharray: effectiveDash } : {})}
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
