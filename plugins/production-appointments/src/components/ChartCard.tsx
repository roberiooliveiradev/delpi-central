import type { ReactNode } from "react";

import { ChartCard as PluginChartCard, chartCardBemClasses } from "@delpi/plugin-ui/index";

const PA_CHART_CARD_CLASSES = chartCardBemClasses("pa", { headerLayout: "titleRow" });

type ChartCardProps = {
  title: string;
  children: ReactNode;
  /** Ajuda no ícone (?) ao lado do título (HelpTooltip do plugin-ui). */
  titleHint?: string;
  /** Subtítulo visível sob o título. */
  hint?: string;
  variant?: "default" | "featured";
  actions?: ReactNode;
};

export function ChartCard({
  title,
  children,
  titleHint,
  hint,
  variant = "default",
  actions,
}: ChartCardProps) {
  return (
    <PluginChartCard
      title={title}
      titleHint={titleHint}
      hint={hint}
      headerActions={actions}
      classNames={PA_CHART_CARD_CLASSES}
      className={variant === "featured" ? "pa-chart-card--featured" : undefined}
    >
      {children}
    </PluginChartCard>
  );
}
