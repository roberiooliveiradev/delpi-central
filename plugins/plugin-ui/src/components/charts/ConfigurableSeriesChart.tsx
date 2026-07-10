import { BarSeriesChart } from "./BarSeriesChart";
import { LineSeriesChart } from "./LineSeriesChart";
import type { SeriesChartKind, SeriesChartOptions, SeriesChartPoint } from "./seriesChartOptions";

export type ConfigurableSeriesChartProps = {
  chartType: SeriesChartKind;
  points: SeriesChartPoint[];
  options?: SeriesChartOptions | null;
  emptyMessage?: string;
  className?: string;
};

/** Despacha para linha ou colunas conforme `chartType`. */
export function ConfigurableSeriesChart({
  chartType,
  points,
  options,
  emptyMessage,
  className,
}: ConfigurableSeriesChartProps) {
  const shared = { points, options, emptyMessage, className };
  if (chartType === "bar") {
    return <BarSeriesChart {...shared} />;
  }
  return <LineSeriesChart {...shared} />;
}
