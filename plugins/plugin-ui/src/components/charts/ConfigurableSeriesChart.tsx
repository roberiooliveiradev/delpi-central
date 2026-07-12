import { BarSeriesChart } from "./BarSeriesChart";
import { LineSeriesChart } from "./LineSeriesChart";
import { ChartPlotAreaGroup } from "./seriesChart";
import { SeriesChartPrimitive } from "./SeriesChartPrimitive";
import type { SeriesChartKind, SeriesChartOptions, SeriesChartPoint } from "./seriesChartOptions";
import type { ChartPartsMap, SeriesChartInteraction } from "./seriesChartParts";

export type ConfigurableSeriesChartProps = {
  chartType: SeriesChartKind;
  points: SeriesChartPoint[];
  options?: SeriesChartOptions | null;
  chartParts?: ChartPartsMap | null;
  interaction?: SeriesChartInteraction | null;
  emptyMessage?: string;
  className?: string;
  /** Rosca (doughnut) quando `chartType === "pie"`. */
  pieInnerRadiusRatio?: number;
};

/** Despacha para o paint SVG conforme `chartType` (4H.7 + kinds avançados). */
export function ConfigurableSeriesChart({
  chartType,
  points,
  options,
  chartParts,
  interaction,
  emptyMessage,
  className,
  pieInnerRadiusRatio = 0,
}: ConfigurableSeriesChartProps) {
  const shared = { points, options, chartParts, interaction, emptyMessage, className };

  if (chartType === "bar") {
    return <BarSeriesChart {...shared} />;
  }
  if (chartType === "line") {
    return <LineSeriesChart {...shared} />;
  }

  return (
    <SeriesChartPrimitive
      {...shared}
      chartType={chartType}
      renderPlotArea={(plotProps) => (
        <ChartPlotAreaGroup {...plotProps} pieInnerRadiusRatio={pieInnerRadiusRatio} />
      )}
    />
  );
}
