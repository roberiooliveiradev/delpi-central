import type { CSSProperties, MouseEvent as ReactMouseEvent, PointerEvent as ReactPointerEvent } from "react";
import {
  ChartTitle,
  SeriesChartClassesProvider,
  SpeedometerGauge,
  chartPartAllowsMove,
  chartPartDomProps,
  getChartPartState,
  isChartPartRefEqual,
  resolveChartAreaStyle,
  resolvePlotAreaStyle,
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
 * `chartArea` = moldura; `plotArea` = fundo interno ao redor do SVG (paridade série).
 */
export function GaugeChartView({ model, options, chartParts, interaction }: Props) {
  const chartArea = resolveChartAreaStyle(options, chartParts);
  const plotArea = resolvePlotAreaStyle(chartParts);
  const interactive = Boolean(interaction);
  const chartAreaRef = { kind: "chartArea" as const };
  const plotAreaRef = { kind: "plotArea" as const };
  const chartAreaDom = chartPartDomProps(chartAreaRef, interaction?.selectedPart);
  const chartAreaSelected = isChartPartRefEqual(chartAreaRef, interaction?.selectedPart);
  const plotAreaSelected = isChartPartRefEqual(plotAreaRef, interaction?.selectedPart);
  const plotAreaDom = chartPartDomProps(plotAreaRef, interaction?.selectedPart);

  const onChartAreaPointerDown = interactive
    ? (event: ReactPointerEvent<HTMLDivElement>) => {
        const host = (event.target as HTMLElement).closest("[data-chart-part]");
        const partId = host?.getAttribute("data-chart-part");
        if (partId && partId !== "chartArea") return;
        event.stopPropagation();
        interaction?.onPartPointerDown?.(chartAreaRef, event);
        if (
          isChartPartRefEqual(chartAreaRef, interaction?.selectedPart) &&
          chartPartAllowsMove(chartAreaRef)
        ) {
          interaction?.onPartMovePointerDown?.(chartAreaRef, event);
        }
      }
    : undefined;

  const onChartAreaDoubleClick = interactive
    ? (event: ReactMouseEvent<HTMLDivElement>) => {
        const host = (event.target as HTMLElement).closest("[data-chart-part]");
        const partId = host?.getAttribute("data-chart-part");
        if (partId && partId !== "chartArea") return;
        event.stopPropagation();
        event.preventDefault();
        interaction?.onPartDoubleClick?.(chartAreaRef, event);
      }
    : undefined;

  const onPlotPointerDown = interactive
    ? (event: ReactPointerEvent<HTMLDivElement>) => {
        const host = (event.target as HTMLElement).closest("[data-chart-part]");
        const partId = host?.getAttribute("data-chart-part");
        if (partId && partId !== "plotArea") return;
        event.stopPropagation();
        interaction?.onPartPointerDown?.(plotAreaRef, event);
        if (
          isChartPartRefEqual(plotAreaRef, interaction?.selectedPart) &&
          chartPartAllowsMove(plotAreaRef)
        ) {
          interaction?.onPartMovePointerDown?.(plotAreaRef, event);
        }
      }
    : undefined;

  const onPlotDoubleClick = interactive
    ? (event: ReactMouseEvent<HTMLDivElement>) => {
        const host = (event.target as HTMLElement).closest("[data-chart-part]");
        const partId = host?.getAttribute("data-chart-part");
        if (partId && partId !== "plotArea") return;
        event.stopPropagation();
        event.preventDefault();
        interaction?.onPartDoubleClick?.(plotAreaRef, event);
      }
    : undefined;

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

  const plotStyle: CSSProperties = {
    flex: 1,
    alignSelf: "stretch",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    boxSizing: "border-box",
    position: "relative",
    minHeight: 0,
    background: plotArea.fill,
    border: `${Math.max(0, plotArea.strokeWidth)}px solid ${plotArea.stroke}`,
    borderRadius: plotArea.borderRadius,
    ...(plotArea.opacity != null ? { opacity: plotArea.opacity } : {}),
  };

  const plotBody =
    model.value == null ? (
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
        showZonesLegend={
          options.showLegend !== false &&
          getChartPartState(chartParts, { kind: "legend" })?.visible !== false
        }
        interaction={interactive ? interaction : null}
        chartParts={chartParts}
        aria-label={model.title || model.label}
      />
    );

  return (
    <SeriesChartClassesProvider prefix={SERIES_CHART_PREFIX}>
      <div
        className={[
          "tdp-gauge-chart",
          interactive ? "tdp-gauge-chart--interactive" : "",
          chartAreaSelected ? "tdp-gauge-chart--part-selected" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        style={hostStyle}
        data-chart-type="gauge"
        {...chartAreaDom}
        onPointerDown={onChartAreaPointerDown}
        onDoubleClick={onChartAreaDoubleClick}
        data-selected={chartAreaSelected ? "true" : undefined}
      >
        <ChartTitle
          title={model.title}
          visible={model.showTitle}
          interaction={interactive ? interaction : null}
          chartParts={chartParts}
        />
        <div
          className={[
            "tdp-gauge-chart__plot",
            plotAreaSelected ? "tdp-gauge-chart__plot--selected" : "",
          ]
            .filter(Boolean)
            .join(" ")}
          style={plotStyle}
          {...plotAreaDom}
          onPointerDown={onPlotPointerDown}
          onDoubleClick={onPlotDoubleClick}
          data-selected={plotAreaSelected ? "true" : undefined}
        >
          {plotBody}
        </div>
      </div>
    </SeriesChartClassesProvider>
  );
}
