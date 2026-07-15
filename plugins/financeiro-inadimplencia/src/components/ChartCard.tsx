import type { ReactNode } from "react";
import { ChartCard as PluginChartCard, chartCardBemClasses } from "@delpi/plugin-ui/index";

const FI_CHART_CARD_CLASSES = chartCardBemClasses("fi");

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
      classNames={FI_CHART_CARD_CLASSES}
      className={className}
    >
      {children}
    </PluginChartCard>
  );
}
