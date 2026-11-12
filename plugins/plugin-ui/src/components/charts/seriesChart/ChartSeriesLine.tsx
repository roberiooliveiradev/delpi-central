import { useSeriesChartClasses } from "../seriesChartClasses";
import { splitFiniteSeriesChartSegments } from "../seriesChartOptions";
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

export type ChartSeriesLineProps = Pick<SeriesChartSharedProps, "layout" | "points" | "seriesColor"> & {
  strokeWidth?: number;
  strokeDasharray?: string;
  plotOn?: "primary" | "secondary";
  interaction?: SeriesChartInteraction | null;
  seriesIndex?: number;
  chartParts?: ChartPartsMap | null;
  /** Curva suave (Catmull-Rom densificada). */
  smooth?: boolean;
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
  smooth = false,
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

  const segments = splitFiniteSeriesChartSegments(visiblePoints);
  if (segments.length === 0) return null;

  const lineClass = [cn.seriesLine, selected ? `${cn.root}__part--selected` : ""]
    .filter(Boolean)
    .join(" ");
  const renderSegment = (segment: (typeof segments)[number], segmentIndex: number) => {
    const anchors = segment.map((point) => ({
      x: toX(point.sourceIndex, points.length),
      y: mapY(Number(point.value)),
    }));
    // 1 ponto: mantém o nó da série (marcador isolado); traço aparece com 2+.
    const strokePoints = resolveSeriesChartStrokePoints(anchors, smooth);
    return (
      <polyline
        key={`line-seg-${seriesIndex}-${segmentIndex}`}
        points={seriesChartPointsAttr(strokePoints)}
        fill="none"
        stroke={seriesColor}
        strokeWidth={effectiveWidth}
        {...(effectiveDash ? { strokeDasharray: effectiveDash } : {})}
        vectorEffect="non-scaling-stroke"
        strokeLinejoin="round"
        strokeLinecap="round"
        className={lineClass}
        {...(segments.length === 1 ? dom : {})}
        onPointerDown={segments.length === 1 ? onPointerDown : undefined}
        onDoubleClick={segments.length === 1 ? onDoubleClick : undefined}
      />
    );
  };

  if (segments.length === 1) {
    return renderSegment(segments[0]!, 0);
  }

  return (
    <g {...dom} onPointerDown={onPointerDown} onDoubleClick={onDoubleClick}>
      {segments.map((segment, segmentIndex) => renderSegment(segment, segmentIndex))}
    </g>
  );
}
