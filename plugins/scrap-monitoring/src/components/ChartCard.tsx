import type { ReactNode } from "react";

import { ChartCard as PluginChartCard, chartCardBemClasses } from "@delpi/plugin-ui/index";

const SM_CHART_CARD_CLASSES = chartCardBemClasses("sm", { headerLayout: "titleRow" });

type ChartCardProps = {
  title: string;
  children: ReactNode;
  empty?: boolean;
};

export function ChartCard({ title, children, empty = false }: ChartCardProps) {
  return (
    <PluginChartCard title={title} classNames={SM_CHART_CARD_CLASSES}>
      {empty ? <p className="sm-chart-card__empty">Sem dados no período.</p> : children}
    </PluginChartCard>
  );
}
