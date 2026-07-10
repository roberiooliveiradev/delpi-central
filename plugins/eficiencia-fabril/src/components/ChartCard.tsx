import type { ReactNode } from "react";

import { ChartCard as PluginChartCard, chartCardBemClasses } from "@delpi/plugin-ui/index";

const EF_CHART_CARD_CLASSES = chartCardBemClasses("ef", {
  headerLayout: "titleRow",
  cardModifier: "chart-card",
});

type ChartCardProps = {
  title: string;
  titleHint?: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
};

export function ChartCard({ title, titleHint, subtitle, actions, children }: ChartCardProps) {
  return (
    <PluginChartCard
      title={title}
      titleHint={titleHint}
      hint={subtitle}
      headerActions={actions}
      classNames={EF_CHART_CARD_CLASSES}
    >
      {children}
    </PluginChartCard>
  );
}
