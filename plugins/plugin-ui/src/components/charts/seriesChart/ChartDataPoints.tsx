import { useSeriesChartClasses } from "../seriesChartClasses";
import type { SeriesChartSharedProps } from "./types";

export type ChartDataPointsProps = Pick<SeriesChartSharedProps, "layout" | "points" | "seriesColor"> & {
  visible?: boolean;
};

export function ChartDataPoints({ layout, points, seriesColor, visible = true }: ChartDataPointsProps) {
  const cn = useSeriesChartClasses();
  if (!visible) return null;

  const { toX, toY } = layout;

  return (
    <>
      {points.map((point, index) => (
        <circle
          key={`dot-${index}`}
          cx={toX(index, points.length)}
          cy={toY(Number(point.value))}
          r={2.5}
          fill={seriesColor}
          className={cn.seriesMarker}
        />
      ))}
    </>
  );
}
