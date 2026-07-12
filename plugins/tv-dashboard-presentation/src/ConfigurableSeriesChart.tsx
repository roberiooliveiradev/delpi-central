import type { ReactNode } from "react";
import {
  ConfigurableSeriesChart as PluginUiConfigurableSeriesChart,
  SeriesChartClassesProvider,
  type ConfigurableSeriesChartProps as PluginUiConfigurableSeriesChartProps,
} from "@delpi/plugin-ui/index";

/**
 * Estilos do gráfico: `@delpi/plugin-ui/styles` (remote MF via preparePluginUiRemote).
 * Não importar CSS por caminho relativo a `plugin-ui/` — quebra o build Docker
 * (contexto sem COPY de plugin-ui).
 */

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
