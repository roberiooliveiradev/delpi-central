import { BarSeriesChart } from "./BarSeriesChart";
import { LineSeriesChart } from "./LineSeriesChart";
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
};

/** Despacha para linha ou colunas conforme `chartType`. */
export function ConfigurableSeriesChart({
  chartType,
  points,
  options,
  chartParts,
  interaction,
  emptyMessage,
  className,
}: ConfigurableSeriesChartProps) {
  const shared = { points, options, chartParts, interaction, emptyMessage, className };
  if (chartType === "bar") {
    return <BarSeriesChart {...shared} />;
  }
  return <LineSeriesChart {...shared} />;
}
