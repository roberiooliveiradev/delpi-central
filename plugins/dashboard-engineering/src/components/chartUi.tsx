import { createDashboardChartToolbarKit } from "@delpi/plugin-ui";

import { CHART_GRANULARITY_OPTIONS, type ChartGranularity } from "../types/chart";

const LABELS = {
  groupAriaLabel: "Agrupamento do gráfico",
  exportSeries: "Exportar série",
  exportSeriesAriaLabel: "Exportar série do gráfico em CSV",
};

const kit = createDashboardChartToolbarKit({ prefix: "ds", labels: LABELS });

type ChartGranularityToggleProps = Omit<
  Parameters<typeof kit.ChartGranularityToggle<ChartGranularity>>[0],
  "options"
>;

type ChartToolbarProps = Omit<
  Parameters<typeof kit.ChartToolbar<ChartGranularity>>[0],
  "options"
>;

export function ChartGranularityToggle(props: ChartGranularityToggleProps) {
  return <kit.ChartGranularityToggle {...props} options={CHART_GRANULARITY_OPTIONS} />;
}

export function ChartToolbar(props: ChartToolbarProps) {
  return <kit.ChartToolbar {...props} options={CHART_GRANULARITY_OPTIONS} />;
}
