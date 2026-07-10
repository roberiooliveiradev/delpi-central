import type { ReactNode } from "react";
import {
  ConfigurableSeriesChart as PluginUiConfigurableSeriesChart,
  SeriesChartClassesProvider,
  type ConfigurableSeriesChartProps as PluginUiConfigurableSeriesChartProps,
} from "@delpi/plugin-ui/index";

export type ConfigurableSeriesChartProps = PluginUiConfigurableSeriesChartProps;

export function ConfigurableSeriesChart(props: ConfigurableSeriesChartProps) {
  return (
    <SeriesChartClassesProvider prefix="tdp-series-chart">
      <PluginUiConfigurableSeriesChart {...props} />
    </SeriesChartClassesProvider>
  );
}

export function ConfigurableSeriesChartWithProvider({
  children,
  prefix = "tdp-series-chart",
}: {
  children: ReactNode;
  prefix?: string;
}) {
  return <SeriesChartClassesProvider prefix={prefix}>{children}</SeriesChartClassesProvider>;
}
