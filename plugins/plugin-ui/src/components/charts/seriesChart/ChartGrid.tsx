import { useSeriesChartClasses } from "../seriesChartClasses";
import type { SeriesChartLayout } from "./layout";

export type ChartGridProps = {
  layout: SeriesChartLayout;
  showHorizontal?: boolean;
  showVertical?: boolean;
  pointCount: number;
};

export function ChartGrid({
  layout,
  showHorizontal = true,
  showVertical = false,
  pointCount,
}: ChartGridProps) {
  const cn = useSeriesChartClasses();
  const { margin, plotW, plotH, ticks, toX, toY } = layout;

  return (
    <>
      {showHorizontal
        ? ticks.map((tick) => {
            const y = toY(tick);
            return (
              <line
                key={`grid-h-${tick}`}
                x1={margin.left}
                y1={y}
                x2={margin.left + plotW}
                y2={y}
                className={cn.gridLine}
              />
            );
          })
        : null}
      {showVertical
        ? Array.from({ length: pointCount }, (_, index) => {
            const x = toX(index, pointCount);
            return (
              <line
                key={`grid-v-${index}`}
                x1={x}
                y1={margin.top}
                x2={x}
                y2={margin.top + plotH}
                className={`${cn.gridLine} ${cn.gridLineVertical}`}
              />
            );
          })
        : null}
    </>
  );
}
