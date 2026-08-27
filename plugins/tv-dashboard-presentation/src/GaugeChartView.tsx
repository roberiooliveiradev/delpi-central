import type { CSSProperties } from "react";
import {
  ChartTitle,
  SeriesChartClassesProvider,
  SpeedometerGauge,
  resolveChartAreaStyle,
  seriesChartThemeStyle,
} from "@delpi/plugin-ui/index";

import type { ComunicadoChartInteraction, ComunicadoChartPartsMap } from "./comunicadoChartParts";
import type { ComunicadoChartOptions } from "./comunicadoChartOptions";
import type { GaugeChartModel } from "./gaugeChartModel";

const SERIES_CHART_PREFIX = "delpi-ui-series-chart";

type Props = {
  model: GaugeChartModel;
  options: ComunicadoChartOptions;
  chartParts?: ComunicadoChartPartsMap | null;
  interaction?: ComunicadoChartInteraction | null;
};

/**
 * Host do velocímetro com chrome/título alinhados ao bloco gráfico (SeriesChart).
 */
export function GaugeChartView({ model, options, chartParts, interaction }: Props) {
  const chartArea = resolveChartAreaStyle(options, chartParts);
  const interactive = Boolean(interaction);
  const hostStyle: CSSProperties = {
    ["--delpi-ui-series-chart-radius" as string]: `${chartArea.borderRadius}px`,
    ["--delpi-ui-series-chart-shadow" as string]: chartArea.boxShadow || "none",
    boxShadow: chartArea.boxShadow,
    borderRadius: chartArea.borderRadius,
    ...seriesChartThemeStyle({ ...options, backgroundColor: chartArea.fill }),
    background: chartArea.fill,
    border: `${Math.max(0, chartArea.strokeWidth)}px solid ${chartArea.stroke}`,
    ...(chartArea.opacity != null ? { opacity: chartArea.opacity } : {}),
    width: "100%",
    height: "100%",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    boxSizing: "border-box",
    position: "relative",
    overflow: "hidden",
  };

  return (
    <SeriesChartClassesProvider prefix={SERIES_CHART_PREFIX}>
      <div className="tdp-gauge-chart" style={hostStyle} data-chart-type="gauge">
        <ChartTitle
          title={model.title}
          visible={model.showTitle}
          interaction={interactive ? interaction : null}
          chartParts={chartParts}
        />
        {model.value == null ? (
          <div className="tdp-data-chart tdp-data-chart--typed">
            <span className="tdp-data-chart__hint">Sem dados</span>
          </div>
        ) : (
          <SpeedometerGauge
            prefix="tdp"
            value={model.value}
            goal={model.goal}
            label={model.label}
            unit={model.unit}
            max={model.max}
            min={model.min}
            accentColor={model.accentColor}
            aria-label={model.title || model.label}
          />
        )}
      </div>
    </SeriesChartClassesProvider>
  );
}
