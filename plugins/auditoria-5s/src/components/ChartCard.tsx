import type { ReactNode } from "react";

import { ChartCard as PluginChartCard, chartCardBemClasses } from "@delpi/plugin-ui";

const A5S_CHART_CARD_CLASSES = chartCardBemClasses("a5s", {
  withHeading: false,
  withActions: false,
  cardModifier: "chart-card",
});

type Props = {
  title: string;
  subtitle?: string;
  children: ReactNode;
};

export function ChartCard({ title, subtitle, children }: Props) {
  return (
    <PluginChartCard
      title={title}
      hint={subtitle}
      titleLevel={3}
      classNames={A5S_CHART_CARD_CLASSES}
    >
      {children}
    </PluginChartCard>
  );
}
