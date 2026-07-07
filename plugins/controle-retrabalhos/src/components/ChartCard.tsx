import type { ReactNode } from "react";

import { ChartCard as PluginChartCard, chartCardBemClasses } from "@delpi/plugin-ui";

const CR_CHART_CARD_CLASSES = chartCardBemClasses("cr", { headerLayout: "titleRow" });

type ChartCardProps = {
  title: string;
  children: ReactNode;
  hint?: string;
  variant?: "default" | "featured";
  actions?: ReactNode;
};

export function ChartCard({
  title,
  children,
  hint,
  variant = "default",
  actions,
}: ChartCardProps) {
  return (
    <PluginChartCard
      title={title}
      hint={hint}
      headerActions={actions}
      classNames={CR_CHART_CARD_CLASSES}
      className={variant === "featured" ? "cr-chart-card--featured" : undefined}
    >
      {children}
    </PluginChartCard>
  );
}
