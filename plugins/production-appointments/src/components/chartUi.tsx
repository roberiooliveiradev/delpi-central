import { createDashboardChartToolbarKit } from "@delpi/plugin-ui/index";

export type SeriesGranularity = "day" | "month";

export const SERIES_GRANULARITY_OPTIONS: {
  value: SeriesGranularity;
  label: string;
}[] = [
  { value: "day", label: "Dia" },
  { value: "month", label: "Mês" },
];

export function resolveSeriesGranularity(suggested: string): SeriesGranularity {
  return suggested === "month" ? "month" : "day";
}

const LABELS = {
  groupAriaLabel: "Granularidade do gráfico",
  exportSeries: "Exportar série",
  exportSeriesAriaLabel: "Exportar série do gráfico",
};

const kit = createDashboardChartToolbarKit({ prefix: "pa", labels: LABELS });

type ChartGranularityToggleProps = Omit<
  Parameters<typeof kit.ChartGranularityToggle<SeriesGranularity>>[0],
  "options"
>;

export function SeriesGranularityToggle(props: ChartGranularityToggleProps) {
  return (
    <kit.ChartGranularityToggle {...props} options={SERIES_GRANULARITY_OPTIONS} />
  );
}
