import {
  ChartCard as DelpiChartCard,
  chartCardBemClasses,
  type ChartCardProps as DelpiChartCardProps,
} from "@delpi/plugin-ui/index";

const CLASS_NAMES = chartCardBemClasses("ppc", {
  headerLayout: "titleRow",
  withActions: true,
  wide: true,
});

export type ChartCardProps = Omit<DelpiChartCardProps, "classNames">;

/** Card de gráfico da gestão à vista — chrome do kit, escopo `ppc`. */
export function ChartCard(props: ChartCardProps) {
  return <DelpiChartCard classNames={CLASS_NAMES} {...props} />;
}
