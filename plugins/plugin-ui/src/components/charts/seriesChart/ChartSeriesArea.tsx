import { useId } from "react";

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
  /** Degradê vertical (cor → transparente) no lugar da opacidade chapada. */
  gradient?: boolean;
};

/** Topo do degradê; a base sempre chega a zero para a área dissolver no plot. */
const GRADIENT_TOP_OPACITY_RATIO = 1;
const GRADIENT_MID_OPACITY_RATIO = 0.45;

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
  gradient = false,
}: ChartSeriesAreaProps) {
  const cn = useSeriesChartClasses();
  const gradientId = `delpi-series-area-fill-${useId().replace(/:/g, "")}-${seriesIndex}`;
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
      {gradient ? (
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={fill} stopOpacity={fillOpacity * GRADIENT_TOP_OPACITY_RATIO} />
            <stop offset="55%" stopColor={fill} stopOpacity={fillOpacity * GRADIENT_MID_OPACITY_RATIO} />
            <stop offset="100%" stopColor={fill} stopOpacity={0} />
          </linearGradient>
        </defs>
      ) : null}
      <polygon
        points={areaPoints}
        fill={gradient ? `url(#${gradientId})` : fill}
        fillOpacity={gradient ? 1 : fillOpacity}
        stroke="none"
      />
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
