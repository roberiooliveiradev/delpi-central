import type { ReactNode } from "react";

import { ChartCard as PluginChartCard, chartCardBemClasses } from "@delpi/plugin-ui/index";

const DS_CHART_CARD_CLASSES = chartCardBemClasses("ds");

type ChartCardProps = {
  title: string;
  children: ReactNode;
  hint?: string;
  titleHint?: string;
  toolbar?: ReactNode;
};

export function ChartCard({ title, children, hint, titleHint, toolbar }: ChartCardProps) {
  return (
    <PluginChartCard
      title={title}
      titleHint={titleHint}
      hint={hint}
      headerActions={toolbar}
      classNames={DS_CHART_CARD_CLASSES}
    >
      {children}
    </PluginChartCard>
  );
}
