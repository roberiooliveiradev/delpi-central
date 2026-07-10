import { useSeriesChartClasses } from "../seriesChartClasses";
import type { SeriesChartLayout } from "./layout";

export type ChartPlotAreaProps = {
  layout: SeriesChartLayout;
  showAxes?: boolean;
};

export function ChartPlotArea({ layout, showAxes = true }: ChartPlotAreaProps) {
  const cn = useSeriesChartClasses();
  const { margin, plotW, plotH } = layout;

  return (
    <rect
      x={margin.left}
      y={margin.top}
      width={plotW}
      height={plotH}
      className={[cn.plotArea, showAxes ? cn.plotAreaAxes : ""].filter(Boolean).join(" ")}
    />
  );
}
