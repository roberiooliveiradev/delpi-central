import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  SERIES_CHART_CATEGORY_PALETTE,
  OFFICE_CHART_SERIES_COLOR,
  resolveSeriesCategoryColor,
} from "../seriesChartOptions";
import {
  bindChartPartPointer,
  filterVisibleSeriesPoints,
  getChartPartState,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import type { SeriesChartSharedProps } from "./types";

export type ChartSeriesFunnelProps = Pick<SeriesChartSharedProps, "layout" | "points" | "seriesColor"> & {
  interaction?: SeriesChartInteraction | null;
  seriesIndex?: number;
  chartParts?: ChartPartsMap | null;
  categoryColors?: string[] | null;
};

/** Funil: trapézios horizontais com largura ∝ valor (estágios de cima para baixo). */
export function ChartSeriesFunnel({
  layout,
  points,
  seriesColor,
  interaction,
  seriesIndex = 0,
  chartParts,
  categoryColors,
}: ChartSeriesFunnelProps) {
  const cn = useSeriesChartClasses();
  const { margin, plotW, plotH, plotInset } = layout;
  const seriesRef = { kind: "series" as const, seriesIndex };
  const seriesVisible = getChartPartState(chartParts, seriesRef)?.visible !== false;
  if (!seriesVisible) return null;

  const visiblePoints = filterVisibleSeriesPoints(points, chartParts, seriesIndex);
  if (visiblePoints.length === 0) return null;

  const values = visiblePoints.map((p) => Math.max(0, Number(p.value) || 0));
  const maxV = Math.max(...values, 1e-6);
  const n = visiblePoints.length;
  const innerW = Math.max(1, plotW - 2 * plotInset);
  const innerH = Math.max(1, plotH - 2 * plotInset);
  const stageH = innerH / n;
  const gap = Math.min(4, stageH * 0.12);
  const cx = margin.left + plotW / 2;

  const { selected, onPointerDown, onDoubleClick, ...dom } = bindChartPartPointer(seriesRef, interaction, {
    moveWhenSelected: false,
  });

  return (
    <g
      className={[cn.seriesFunnel, selected ? `${cn.root}__part--selected` : ""]
        .filter(Boolean)
        .join(" ")}
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    >
      {visiblePoints.map((point, i) => {
        const topW = (values[i]! / maxV) * innerW;
        const next = values[i + 1] ?? values[i]!;
        const botW = (next / maxV) * innerW;
        const y0 = margin.top + plotInset + i * stageH + gap / 2;
        const y1 = margin.top + plotInset + (i + 1) * stageH - gap / 2;
        const path = [
          `M ${cx - topW / 2} ${y0}`,
          `L ${cx + topW / 2} ${y0}`,
          `L ${cx + botW / 2} ${y1}`,
          `L ${cx - botW / 2} ${y1}`,
          "Z",
        ].join(" ");
        const fill = resolveSeriesCategoryColor(
          i,
          seriesColor || OFFICE_CHART_SERIES_COLOR,
          categoryColors,
          SERIES_CHART_CATEGORY_PALETTE,
        );
        return (
          <path
            key={`funnel-${point.sourceIndex}`}
            d={path}
            fill={fill}
            stroke="#ffffff"
            strokeWidth={1}
          />
        );
      })}
    </g>
  );
}
