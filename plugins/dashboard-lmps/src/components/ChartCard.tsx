import {
  ChartCard as DelpiChartCard,
  type ChartCardClassNames,
  type ChartCardProps as DelpiChartCardProps,
} from "@delpi/plugin-ui/index";

const CLASS_NAMES = {
  section: "lmps-card lmps-chart-card",
  header: "lmps-card-header",
  title: "",
  titleHelp: "lmps-chart-card__title-help",
  body: "lmps-card-body",
} satisfies ChartCardClassNames;

export type ChartCardProps = Omit<DelpiChartCardProps, "classNames" | "titleLevel">;

export function ChartCard(props: ChartCardProps) {
  return <DelpiChartCard classNames={CLASS_NAMES} titleLevel={3} {...props} />;
}
