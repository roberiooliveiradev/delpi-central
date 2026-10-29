import {
  ChartCard as DelpiChartCard,
  chartCardBemClasses,
  delpiUiClass,
  type ChartCardProps as DelpiChartCardProps,
} from "@delpi/plugin-ui/index";

const BASE = chartCardBemClasses("lmps");

/** Mantém aliases locais (`lmps-card-header` / `lmps-card-body`) + dual kit. */
const CLASS_NAMES = {
  ...BASE,
  header: delpiUiClass("lmps-card-header", "delpi-ui-chart-card__header"),
  body: delpiUiClass("lmps-card-body", "delpi-ui-chart-card__body"),
};

export type ChartCardProps = Omit<DelpiChartCardProps, "classNames" | "titleLevel">;

export function ChartCard(props: ChartCardProps) {
  return <DelpiChartCard classNames={CLASS_NAMES} titleLevel={3} {...props} />;
}
