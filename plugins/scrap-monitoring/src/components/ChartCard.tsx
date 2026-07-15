import type { ReactNode } from "react";

import { ChartCard as PluginChartCard, chartCardBemClasses } from "@delpi/plugin-ui/index";

const SM_CHART_CARD_WIDE = chartCardBemClasses("sm", {
  headerLayout: "titleRow",
  wide: true,
});

const SM_CHART_CARD_HALF = chartCardBemClasses("sm", {
  headerLayout: "titleRow",
  wide: false,
});

type ChartCardProps = {
  title: string;
  titleHint?: string;
  children: ReactNode;
  empty?: boolean;
  /** `false` = metade da grade (pares lado a lado). */
  wide?: boolean;
  className?: string;
};

export function ChartCard({
  title,
  titleHint,
  children,
  empty = false,
  wide = true,
  className,
}: ChartCardProps) {
  return (
    <PluginChartCard
      title={title}
      titleHint={titleHint}
      classNames={wide ? SM_CHART_CARD_WIDE : SM_CHART_CARD_HALF}
      className={className}
    >
      {empty ? <p className="sm-chart-card__empty">Sem dados no período.</p> : children}
    </PluginChartCard>
  );
}
