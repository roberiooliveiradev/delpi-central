import {
  MultiTypeSeriesChart,
  type MultiTypeSeriesChartProps,
  type MultiTypeSeriesSpec,
} from "@delpi/plugin-ui/index";

export type GroupedColumnBarSpec = MultiTypeSeriesSpec;

export type GroupedColumnSeriesChartProps = Omit<
  MultiTypeSeriesChartProps,
  "series" | "chartType"
> & {
  bars: ReadonlyArray<GroupedColumnBarSpec>;
};

/**
 * Compat wrapper around kit MultiTypeSeriesChart (fixed column type).
 * Prefer ChartViewShell + MultiTypeSeriesChart for new surfaces.
 */
export function GroupedColumnSeriesChart({
  bars,
  ...rest
}: GroupedColumnSeriesChartProps) {
  return <MultiTypeSeriesChart {...rest} series={bars} chartType="column" />;
}
