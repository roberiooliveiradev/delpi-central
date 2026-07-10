import type { ReactNode } from "react";

import { ChartCard as PluginChartCard, chartCardBemClasses } from "@delpi/plugin-ui/index";

const PAC_CHART_CARD_CLASSES = chartCardBemClasses("pac");

type ChartCardProps = {
  title: string;
  children: ReactNode;
  hint?: string;
};

export function ChartCard({ title, children, hint }: ChartCardProps) {
  return (
    <PluginChartCard title={title} titleHint={hint} classNames={PAC_CHART_CARD_CLASSES}>
      {children}
    </PluginChartCard>
  );
}
