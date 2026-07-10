import { useSeriesChartClasses } from "../seriesChartClasses";
import { formatChartTick } from "./layout";
import type { SeriesChartKindProps } from "./types";

export type ChartValueLabelsProps = Pick<
  SeriesChartKindProps,
  "chartType" | "layout" | "points" | "valueFormat"
> & {
  visible?: boolean;
};

export function ChartValueLabels({
  chartType,
  layout,
  points,
  valueFormat,
  visible = true,
}: ChartValueLabelsProps) {
  const cn = useSeriesChartClasses();
  if (!visible) return null;

  const { margin, plotW, plotH, toX, toY } = layout;

  if (chartType === "bar") {
    return (
      <>
        {points.map((point, index) => {
          const value = Number(point.value);
          const barW = plotW / Math.max(points.length, 1);
          const gap = Math.min(barW * 0.2, 8);
          const width = Math.max(barW - gap, 2);
          const x = margin.left + index * barW + gap / 2;
          const y = toY(value);

          return (
            <text
              key={`bar-label-${index}`}
              x={x + width / 2}
              y={y - 4}
              className={cn.dataLabel}
              textAnchor="middle"
            >
              {formatChartTick(value, valueFormat)}
            </text>
          );
        })}
      </>
    );
  }

  return (
    <>
      {points.map((point, index) => (
        <text
          key={`line-label-${index}`}
          x={toX(index, points.length)}
          y={toY(Number(point.value)) - 6}
          className={cn.dataLabel}
          textAnchor="middle"
        >
          {formatChartTick(Number(point.value), valueFormat)}
        </text>
      ))}
    </>
  );
}
