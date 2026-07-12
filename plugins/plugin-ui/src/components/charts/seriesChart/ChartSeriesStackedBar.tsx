import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  SERIES_CHART_CATEGORY_PALETTE,
  OFFICE_CHART_SERIES_COLOR,
} from "../seriesChartOptions";
import {
  bindChartPartPointer,
  filterVisibleSeriesPoints,
  getChartPartState,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import type { SeriesChartSharedProps } from "./types";

export type ChartSeriesStackedBarProps = Pick<SeriesChartSharedProps, "layout" | "points" | "seriesColor"> & {
  interaction?: SeriesChartInteraction | null;
  seriesIndex?: number;
  chartParts?: ChartPartsMap | null;
};

/**
 * Empilhado (série única MVP): trata cada ponto como segmento de **uma** coluna
 * central — labels viram identidade de cor (legenda implícita pelas fatias).
 * Multi-série / categorias empilhadas ficam para evolução futura.
 */
export function ChartSeriesStackedBar({
  layout,
  points,
  seriesColor,
  interaction,
  seriesIndex = 0,
  chartParts,
}: ChartSeriesStackedBarProps) {
  const cn = useSeriesChartClasses();
  const { margin, plotW, plotH, plotInset } = layout;
  const seriesRef = { kind: "series" as const, seriesIndex };
  const seriesVisible = getChartPartState(chartParts, seriesRef)?.visible !== false;
  if (!seriesVisible) return null;

  const visiblePoints = filterVisibleSeriesPoints(points, chartParts, seriesIndex);
  if (visiblePoints.length === 0) return null;

  const values = visiblePoints.map((p) => Math.max(0, Number(p.value) || 0));
  const total = values.reduce((sum, v) => sum + v, 0);
  if (total <= 0) return null;

  const innerH = Math.max(1, plotH - 2 * plotInset);
  const barW = Math.max(12, Math.min(plotW * 0.28, 64));
  const x = margin.left + (plotW - barW) / 2;
  const baseY = margin.top + plotInset + innerH;

  const { selected, onPointerDown, onDoubleClick, ...dom } = bindChartPartPointer(seriesRef, interaction, {
    moveWhenSelected: false,
  });

  let fromBottom = 0;
  return (
    <g
      className={[cn.seriesStackedBar, selected ? `${cn.root}__part--selected` : ""]
        .filter(Boolean)
        .join(" ")}
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    >
      {visiblePoints.map((point, i) => {
        const value = values[i]!;
        const segH = (value / total) * innerH;
        const y = baseY - fromBottom - segH;
        fromBottom += segH;
        const fill =
          i === 0
            ? seriesColor || OFFICE_CHART_SERIES_COLOR
            : SERIES_CHART_CATEGORY_PALETTE[i % SERIES_CHART_CATEGORY_PALETTE.length]!;
        return (
          <rect
            key={`stack-${point.sourceIndex}`}
            x={x}
            y={y}
            width={barW}
            height={Math.max(segH, 0.5)}
            fill={fill}
            stroke="#ffffff"
            strokeWidth={0.75}
            rx={1}
          />
        );
      })}
    </g>
  );
}
