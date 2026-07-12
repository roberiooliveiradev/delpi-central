import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  CHART_MARKER_RADIUS,
  bindChartPartPointer,
  filterVisibleSeriesPoints,
  getChartPartState,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import type { SeriesChartSharedProps } from "./types";

export type ChartSeriesScatterProps = Pick<SeriesChartSharedProps, "layout" | "points" | "seriesColor"> & {
  interaction?: SeriesChartInteraction | null;
  seriesIndex?: number;
  chartParts?: ChartPartsMap | null;
};

/** Dispersão: círculos em (índice ou rótulo numérico, valor) — sem linha. */
export function ChartSeriesScatter({
  layout,
  points,
  seriesColor,
  interaction,
  seriesIndex = 0,
  chartParts,
}: ChartSeriesScatterProps) {
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

  const { selected, onPointerDown, onDoubleClick, ...dom } = bindChartPartPointer(seriesRef, interaction, {
    moveWhenSelected: false,
  });

  return (
    <g
      className={[cn.seriesScatter, selected ? `${cn.root}__part--selected` : ""]
        .filter(Boolean)
        .join(" ")}
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    >
      {visiblePoints.map((point, i) => {
        const cx = allNumeric
          ? margin.left + plotInset + ((numericXs[i]! - xMin) / xRange) * innerW
          : toX(point.sourceIndex, points.length);
        const cy = toY(Number(point.value));
        return (
          <circle
            key={`scatter-${point.sourceIndex}`}
            cx={cx}
            cy={cy}
            r={CHART_MARKER_RADIUS + 1.5}
            fill={seriesColor}
            stroke="#ffffff"
            strokeWidth={1}
          />
        );
      })}
    </g>
  );
}
