import { useSeriesChartClasses } from "../seriesChartClasses";
import { formatChartTick, type SeriesChartLayout } from "./layout";
import type { SeriesChartValueFormat } from "../seriesChartOptions";

export type ChartAxisYProps = {
  layout: SeriesChartLayout;
  showLabels?: boolean;
  showTitle?: boolean;
  title?: string;
  valueFormat: SeriesChartValueFormat;
};

export function ChartAxisY({
  layout,
  showLabels = true,
  showTitle = false,
  title,
  valueFormat,
}: ChartAxisYProps) {
  const cn = useSeriesChartClasses();
  const { margin, plotH, ticks, toY } = layout;
  const axisCenterY = margin.top + plotH / 2;

  return (
    <>
      {showTitle && title ? (
        <text
          x={10}
          y={axisCenterY}
          className={`${cn.axisTitle} ${cn.axisTitleY}`}
          transform={`rotate(-90 10 ${axisCenterY})`}
        >
          {title}
        </text>
      ) : null}
      {showLabels
        ? ticks.map((tick) => {
            const y = toY(tick);
            return (
              <text
                key={`y-${tick}`}
                x={margin.left - 6}
                y={y}
                className={`${cn.tick} ${cn.tickY}`}
                textAnchor="end"
                dominantBaseline="middle"
              >
                {formatChartTick(tick, valueFormat)}
              </text>
            );
          })
        : null}
    </>
  );
}
