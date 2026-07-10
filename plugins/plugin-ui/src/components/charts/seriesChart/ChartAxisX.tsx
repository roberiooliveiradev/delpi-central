import { useSeriesChartClasses } from "../seriesChartClasses";
import type { SeriesChartLayout } from "./layout";
import type { SeriesChartPoint } from "../seriesChartOptions";

export type ChartAxisXProps = {
  layout: SeriesChartLayout;
  points: SeriesChartPoint[];
  showLabels?: boolean;
  showTitle?: boolean;
  title?: string;
};

export function ChartAxisX({
  layout,
  points,
  showLabels = true,
  showTitle = false,
  title,
}: ChartAxisXProps) {
  const cn = useSeriesChartClasses();
  const { margin, plotH, viewH, xLabelStep, xLabelsRotated, toX } = layout;
  const xAxisY = margin.top + plotH;
  const labelY = xLabelsRotated ? xAxisY + 18 : xAxisY + 14;

  return (
    <>
      {showLabels
        ? points.map((point, index) => {
            if (index % xLabelStep !== 0 && index !== points.length - 1) return null;
            const x = toX(index, points.length);
            const label = String(point.label ?? index + 1);
            const className = [cn.tick, cn.tickX, xLabelsRotated ? cn.tickXRotated : ""]
              .filter(Boolean)
              .join(" ");

            return (
              <text
                key={`x-${index}`}
                x={x}
                y={labelY}
                className={className}
                textAnchor={xLabelsRotated ? "end" : "middle"}
                transform={xLabelsRotated ? `rotate(-38 ${x} ${labelY})` : undefined}
              >
                {label}
              </text>
            );
          })
        : null}
      {showTitle && title ? (
        <text
          x={margin.left + layout.plotW / 2}
          y={viewH - 4}
          className={`${cn.axisTitle} ${cn.axisTitleX}`}
          textAnchor="middle"
        >
          {title}
        </text>
      ) : null}
    </>
  );
}
