import { useSeriesChartClasses } from "../seriesChartClasses";
import type { SeriesChartSharedProps } from "./types";

export type ChartSeriesLineProps = Pick<SeriesChartSharedProps, "layout" | "points" | "seriesColor">;

export function ChartSeriesLine({ layout, points, seriesColor }: ChartSeriesLineProps) {
  const cn = useSeriesChartClasses();
  const { toX, toY } = layout;

  return (
    <polyline
      points={points.map((point, index) => `${toX(index, points.length)},${toY(Number(point.value))}`).join(" ")}
      fill="none"
      stroke={seriesColor}
      strokeWidth={2}
      vectorEffect="non-scaling-stroke"
      strokeLinejoin="round"
      strokeLinecap="round"
      className={cn.seriesLine}
    />
  );
}
