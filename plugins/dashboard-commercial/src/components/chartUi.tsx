import { createDashboardChartToolbarKit } from "@delpi/plugin-ui";

import { COMMERCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";
import { CHART_GRANULARITY_OPTIONS, type ChartGranularity } from "../types/chart";

const LABELS = {
  groupAriaLabel: "Agrupamento do gráfico",
  exportSeries: "Exportar série",
  exportSeriesAriaLabel: "Exportar série do gráfico em CSV",
};

const kit = createDashboardChartToolbarKit({ prefix: "dc", labels: LABELS });

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

export function ChartToolbar({
  exportHelp,
  granularityHelp,
  exportActions,
  onExportCsv,
  ...props
}: ChartToolbarProps) {
  return (
    <kit.ChartToolbar
      {...props}
      options={CHART_GRANULARITY_OPTIONS}
      exportActions={exportActions}
      onExportCsv={onExportCsv}
      granularityHelp={granularityHelp ?? COMMERCIAL_HELP_TOOLTIPS.charts.rolGranularity}
      exportHelp={
        exportHelp ??
        (!exportActions && onExportCsv ? COMMERCIAL_HELP_TOOLTIPS.charts.rolExport : undefined)
      }
    />
  );
}
