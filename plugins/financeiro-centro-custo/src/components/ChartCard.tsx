import type { ReactNode } from "react";

import { ChartCard as PluginChartCard, chartCardBemClasses } from "@delpi/plugin-ui/index";

const FCC_CHART_CARD_CLASSES = chartCardBemClasses("fcc");

type ChartCardProps = {
  title: string;
  children: ReactNode;
  hint?: string;
  className?: string;
  headerActions?: ReactNode;
};

export function ChartCard({ title, children, hint, className, headerActions }: ChartCardProps) {
  return (
    <PluginChartCard
      title={title}
      hint={hint}
      headerActions={headerActions}
      classNames={FCC_CHART_CARD_CLASSES}
      className={className}
    >
      {children}
    </PluginChartCard>
  );
}
