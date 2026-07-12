import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  bindChartPartPointer,
  filterVisibleSeriesPoints,
  getChartPartState,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import type { SeriesChartSharedProps } from "./types";

export type ChartSeriesHistogramProps = Pick<SeriesChartSharedProps, "layout" | "points" | "seriesColor"> & {
  interaction?: SeriesChartInteraction | null;
  seriesIndex?: number;
  chartParts?: ChartPartsMap | null;
};

const TARGET_BINS = 8;

/** Agrupa valores em ~8 bins e pinta como colunas de frequência. */
export function ChartSeriesHistogram({
  layout,
  points,
  seriesColor,
  interaction,
  seriesIndex = 0,
  chartParts,
}: ChartSeriesHistogramProps) {
  const cn = useSeriesChartClasses();
  const { margin, plotW, plotH, plotInset } = layout;
  const seriesRef = { kind: "series" as const, seriesIndex };
  const seriesVisible = getChartPartState(chartParts, seriesRef)?.visible !== false;
  if (!seriesVisible) return null;

  const visiblePoints = filterVisibleSeriesPoints(points, chartParts, seriesIndex);
  if (visiblePoints.length === 0) return null;

  const values = visiblePoints.map((p) => Number(p.value)).filter((v) => Number.isFinite(v));
  if (values.length === 0) return null;

  const min = Math.min(...values);
  const max = Math.max(...values);
  const binCount = Math.max(1, Math.min(TARGET_BINS, values.length));
  const span = max - min || 1;
  const binWidth = span / binCount;
  const counts = Array.from({ length: binCount }, () => 0);
  for (const value of values) {
    const idx = value >= max ? binCount - 1 : Math.min(binCount - 1, Math.floor((value - min) / binWidth));
    counts[idx] = (counts[idx] ?? 0) + 1;
  }
  const maxCount = Math.max(...counts, 1);
  const innerH = Math.max(1, plotH - 2 * plotInset);
  const slotW = plotW / binCount;
  const gap = Math.min(slotW * 0.15, 6);

  const { selected, onPointerDown, onDoubleClick, ...dom } = bindChartPartPointer(seriesRef, interaction, {
    moveWhenSelected: false,
  });

  return (
    <g
      className={[cn.seriesHistogram, selected ? `${cn.root}__part--selected` : ""]
        .filter(Boolean)
        .join(" ")}
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    >
      {counts.map((count, index) => {
        const height = (count / maxCount) * innerH;
        const width = Math.max(slotW - gap, 2);
        const x = margin.left + index * slotW + gap / 2;
        const y = margin.top + plotInset + innerH - height;
        return (
          <rect
            key={`hist-${index}`}
            x={x}
            y={y}
            width={width}
            height={Math.max(height, count > 0 ? 1 : 0)}
            fill={seriesColor}
            rx={1}
          />
        );
      })}
    </g>
  );
}
