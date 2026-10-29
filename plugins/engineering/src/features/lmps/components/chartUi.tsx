import { EngineeringChartToolbarKit } from "../../../ui/engineeringUi";

import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { CHART_GRANULARITY_OPTIONS, type ChartGranularity } from "../types/chart";

const kit = EngineeringChartToolbarKit;

type ChartGranularityToggleProps = Omit<
  Parameters<typeof kit.ChartGranularityToggle<ChartGranularity>>[0],
  "options"
>;

type ChartToolbarProps = Omit<
  Parameters<typeof kit.ChartToolbar<ChartGranularity>>[0],
  "options" | "granularityField"
>;

export function ChartGranularityToggle(props: ChartGranularityToggleProps) {
  return <kit.ChartGranularityToggle {...props} options={CHART_GRANULARITY_OPTIONS} />;
}

export function ChartToolbar(props: ChartToolbarProps) {
  return (
    <kit.ChartToolbar
      {...props}
      options={CHART_GRANULARITY_OPTIONS}
      granularityField={{
        label: "Agrupamento",
        hint: LMPS_HELP_TOOLTIPS.charts.evolutionGranularity,
      }}
    />
  );
}
