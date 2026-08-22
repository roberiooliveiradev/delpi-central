import {
  ChartCard as DelpiChartCard,
  chartCardBemClasses,
  createDashboardKpiCard,
  createDashboardLoadingActivityCard,
  type ChartCardProps as DelpiChartCardProps,
} from "@delpi/plugin-ui/index";

import { copy } from "../content/copy";

/** Chrome do kit com escopo `fin` — o MFE não redefine CSS de componente. */
export const FinKpiCard = createDashboardKpiCard({
  prefix: "fin",
  labels: {
    goalPrefix: copy.home.goalLabel,
    iddScorePrefix: copy.home.iddLabel,
    badgesStatus: "Indicadores do cartão",
  },
});

export const FinLoadingCard = createDashboardLoadingActivityCard({
  prefix: "fin",
  labels: {
    progressRemaining: (n) => `Faltam ${n}%`,
    progressAriaDeterminate: (n) => `Faltam ${n} por cento`,
    progressAriaIndeterminate: copy.home.loading,
  },
});

const CHART_CARD_CLASSES = chartCardBemClasses("fin", {
  headerLayout: "titleRow",
  withActions: true,
  wide: true,
});

export type FinChartCardProps = Omit<DelpiChartCardProps, "classNames">;

export function FinChartCard(props: FinChartCardProps) {
  return <DelpiChartCard classNames={CHART_CARD_CLASSES} {...props} />;
}
