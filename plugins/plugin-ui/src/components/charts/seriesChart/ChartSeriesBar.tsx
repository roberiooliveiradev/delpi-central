import { useSeriesChartClasses } from "../seriesChartClasses";
import type { SeriesChartSharedProps } from "./types";

export type ChartSeriesBarProps = Pick<SeriesChartSharedProps, "layout" | "points" | "seriesColor">;

export function ChartSeriesBar({ layout, points, seriesColor }: ChartSeriesBarProps) {
  const cn = useSeriesChartClasses();
  const { margin, plotW, plotH, toY } = layout;

  return (
    <>
      {points.map((point, index) => {
        const value = Number(point.value);
        const barW = plotW / Math.max(points.length, 1);
        const gap = Math.min(barW * 0.2, 8);
        const width = Math.max(barW - gap, 2);
        const x = margin.left + index * barW + gap / 2;
        const y = toY(value);
        const height = margin.top + plotH - y;

        return (
          <rect
            key={`bar-${index}`}
            x={x}
            y={y}
            width={width}
            height={height}
            fill={seriesColor}
            rx={1}
            className={cn.seriesBar}
          />
        );
      })}
    </>
  );
}
