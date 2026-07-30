import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  bindChartPartPointer,
  filterVisibleSeriesPoints,
  getChartPartState,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import type { SeriesChartSharedProps } from "./types";

export type ChartSeriesBubbleProps = Pick<SeriesChartSharedProps, "layout" | "points" | "seriesColor"> & {
  interaction?: SeriesChartInteraction | null;
  seriesIndex?: number;
  chartParts?: ChartPartsMap | null;
};

export const SERIES_CHART_BUBBLE_MIN_R = 4;
export const SERIES_CHART_BUBBLE_MAX_R = 22;

/** Bolhas: X numérico (ou índice), Y = value, raio ∝ size (fallback |value|). */
export function ChartSeriesBubble({
  layout,
  points,
  seriesColor,
  interaction,
  seriesIndex = 0,
  chartParts,
}: ChartSeriesBubbleProps) {
  const cn = useSeriesChartClasses();
  const { toX, toY, margin, plotW, plotInset } = layout;
  const seriesRef = { kind: "series" as const, seriesIndex };
  const seriesVisible = getChartPartState(chartParts, seriesRef)?.visible !== false;
  if (!seriesVisible) return null;

  const visiblePoints = filterVisibleSeriesPoints(points, chartParts, seriesIndex);
  if (visiblePoints.length === 0) return null;

  const numericXs = visiblePoints.map((p) => {
    const n = p.label != null && String(p.label).trim() !== "" ? Number(p.label) : NaN;
    return Number.isFinite(n) ? n : null;
  });
  const allNumeric = numericXs.every((n) => n != null);
  const xMin = allNumeric ? Math.min(...(numericXs as number[])) : 0;
  const xMax = allNumeric ? Math.max(...(numericXs as number[])) : 1;
  const xRange = Math.max(xMax - xMin, 1e-6);
  const innerW = Math.max(1, plotW - 2 * plotInset);

  const sizeValues = visiblePoints.map((p) => {
    if (p.size != null && Number.isFinite(Number(p.size))) return Math.abs(Number(p.size));
    return Math.abs(Number(p.value) || 0);
  });
  const maxSize = Math.max(...sizeValues, 1e-6);

  const { selected, onPointerDown, onDoubleClick, ...dom } = bindChartPartPointer(seriesRef, interaction, {
    moveWhenSelected: false,
  });

  return (
    <g
      className={[cn.seriesBubble, selected ? `${cn.root}__part--selected` : ""]
        .filter(Boolean)
        .join(" ")}
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    >
      {visiblePoints.map((point, i) => {
        const sizeAbs = sizeValues[i]!;
        const r =
          SERIES_CHART_BUBBLE_MIN_R +
          Math.sqrt(sizeAbs / maxSize) * (SERIES_CHART_BUBBLE_MAX_R - SERIES_CHART_BUBBLE_MIN_R);
        const cx = allNumeric
          ? margin.left + plotInset + ((numericXs[i]! - xMin) / xRange) * innerW
          : toX(point.sourceIndex ?? i, points.length);
        const cy = toY(Number(point.value));
        return (
          <circle
            key={`bubble-${point.sourceIndex ?? i}`}
            cx={cx}
            cy={cy}
            r={r}
            fill={seriesColor}
            fillOpacity={0.55}
            stroke={seriesColor}
            strokeWidth={1.25}
          />
        );
      })}
    </g>
  );
}
