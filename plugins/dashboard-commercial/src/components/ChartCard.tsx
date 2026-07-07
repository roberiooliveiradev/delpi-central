import {
  ChartCard as DelpiChartCard,
  chartCardBemClasses,
  type ChartCardProps as DelpiChartCardProps,
} from "@delpi/plugin-ui";

const CLASS_NAMES = chartCardBemClasses("dc");

export type ChartCardProps = Omit<DelpiChartCardProps, "classNames">;

export function ChartCard(props: ChartCardProps) {
  return <DelpiChartCard classNames={CLASS_NAMES} {...props} />;
}
