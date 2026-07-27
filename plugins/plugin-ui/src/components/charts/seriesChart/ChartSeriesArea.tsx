import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  CHART_SERIES_LINE_STROKE_WIDTH,
  bindChartPartPointer,
  filterVisibleSeriesPoints,
  getChartPartState,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import {
  resolveSeriesChartStrokePoints,
  seriesChartPointsAttr,
} from "../seriesChartCurve";
import type { SeriesChartSharedProps } from "./types";

export type ChartSeriesAreaProps = Pick<SeriesChartSharedProps, "layout" | "points" | "seriesColor"> & {
  strokeWidth?: number;
  interaction?: SeriesChartInteraction | null;
  seriesIndex?: number;
  chartParts?: ChartPartsMap | null;
  /** Opacidade do preenchimento (0–1). */
  fillOpacity?: number;
  /** Contorno/área com curva suave. */
  smooth?: boolean;
};

/** Área sob a série — primitivo `area` + contorno `line` (4H.7). */
export function ChartSeriesArea({
  layout,
  points,
  seriesColor,
  strokeWidth = CHART_SERIES_LINE_STROKE_WIDTH,
  interaction,
  seriesIndex = 0,
  chartParts,
  fillOpacity = 0.35,
  smooth = false,
}: ChartSeriesAreaProps) {
  const cn = useSeriesChartClasses();
  const { toX, toY, margin, plotH } = layout;
  const ref = { kind: "series" as const, seriesIndex };
  const seriesVisible = getChartPartState(chartParts, ref)?.visible !== false;
  if (!seriesVisible) return null;

  const visiblePoints = filterVisibleSeriesPoints(points, chartParts, seriesIndex);
  if (visiblePoints.length === 0) return null;

  const { selected, onPointerDown, onDoubleClick, ...dom } = bindChartPartPointer(ref, interaction, {
    moveWhenSelected: false,
  });

  const baseline = margin.top + plotH;
  const anchors = visiblePoints.map((point) => ({
    x: toX(point.sourceIndex, points.length),
    y: toY(Number(point.value)),
  }));
  const topCurve = resolveSeriesChartStrokePoints(anchors, smooth);
  const topPoints = seriesChartPointsAttr(topCurve);
  const first = topCurve[0]!;
  const last = topCurve[topCurve.length - 1]!;
  const areaPoints = [`${first.x},${baseline}`, topPoints, `${last.x},${baseline}`].join(" ");

  const fill = getChartPartState(chartParts, ref)?.style?.fill ?? seriesColor;

  return (
    <g
      className={[cn.seriesArea, selected ? `${cn.root}__part--selected` : ""].filter(Boolean).join(" ")}
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    >
      <polygon points={areaPoints} fill={fill} fillOpacity={fillOpacity} stroke="none" />
      <polyline
        points={topPoints}
        fill="none"
        stroke={seriesColor}
        strokeWidth={strokeWidth}
        vectorEffect="non-scaling-stroke"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </g>
  );
}
