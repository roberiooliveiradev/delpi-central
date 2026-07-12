import type { ReactNode } from "react";
import {
  ConfigurableSeriesChart as PluginUiConfigurableSeriesChart,
  SeriesChartClassesProvider,
  type ConfigurableSeriesChartProps as PluginUiConfigurableSeriesChartProps,
} from "@delpi/plugin-ui/index";

/** CSS canônico do gráfico de séries (fonte única: plugin-ui). */
import "../../plugin-ui/src/styles/series-chart.css";

export type ConfigurableSeriesChartProps = PluginUiConfigurableSeriesChartProps;

/** Prefixo BEM padrão do plugin-ui (`delpi-ui-series-chart`). */
const DEFAULT_SERIES_CHART_PREFIX = "delpi-ui-series-chart";

export function ConfigurableSeriesChart(props: ConfigurableSeriesChartProps) {
  return (
    <SeriesChartClassesProvider prefix={DEFAULT_SERIES_CHART_PREFIX}>
      <PluginUiConfigurableSeriesChart {...props} />
    </SeriesChartClassesProvider>
  );
}

export function ConfigurableSeriesChartWithProvider({
  children,
  prefix = DEFAULT_SERIES_CHART_PREFIX,
}: {
  children: ReactNode;
  prefix?: string;
}) {
  return <SeriesChartClassesProvider prefix={prefix}>{children}</SeriesChartClassesProvider>;
}
