import { useSeriesChartClasses } from "../seriesChartClasses";
import type { SeriesChartLayout } from "./layout";

export type ChartAxisLinesProps = {
  layout: SeriesChartLayout;
  visible?: boolean;
};

export function ChartAxisLines({ layout, visible = true }: ChartAxisLinesProps) {
  const cn = useSeriesChartClasses();
  if (!visible) return null;

  const { margin, plotW, plotH } = layout;
  const xAxisY = margin.top + plotH;

  return (
    <>
      <line x1={margin.left} y1={xAxisY} x2={margin.left + plotW} y2={xAxisY} className={cn.axisLine} />
      <line x1={margin.left} y1={margin.top} x2={margin.left} y2={xAxisY} className={cn.axisLine} />
    </>
  );
}
