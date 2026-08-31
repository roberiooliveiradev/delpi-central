import type { CSSProperties, MouseEvent as ReactMouseEvent, PointerEvent as ReactPointerEvent } from "react";
import {
  ChartContainer,
  ChartPartResizeHandles,
  ChartPlotAreaChrome,
  ChartTitle,
  SeriesChartClassesProvider,
  SpeedometerGauge,
  chartPartAllowsMove,
  chartPartAllowsResize,
  chartPartDomProps,
  clampChartPartFrame,
  getChartPartState,
  isChartPartRefEqual,
  isFullBleedChartAreaFrame,
  resolveChartAreaStyle,
  resolvePlotAreaStyle,
  seriesChartThemeStyle,
  useSeriesChartClasses,
} from "@delpi/plugin-ui/index";

import type { ComunicadoChartInteraction, ComunicadoChartPartsMap } from "./comunicadoChartParts";
import type { ComunicadoChartOptions } from "./comunicadoChartOptions";
import type { GaugeChartModel } from "./gaugeChartModel";

const SERIES_CHART_PREFIX = "delpi-ui-series-chart";

/** Layout full-bleed para ChartPlotAreaChrome (handles em % do plotHost). */
const GAUGE_FULL_BLEED_PLOT_LAYOUT = {
  viewW: 100,
  viewH: 100,
  plotW: 100,
  plotH: 100,
  margin: { top: 0, right: 0, bottom: 0, left: 0 },
};

type Props = {
  model: GaugeChartModel;
  options: ComunicadoChartOptions;
  chartParts?: ComunicadoChartPartsMap | null;
  interaction?: ComunicadoChartInteraction | null;
};

/**
 * Host do velocímetro no mesmo chrome da série (shell + ChartContainer + plotHost).
 * `chartArea` = moldura; `plotArea` = fundo + ChartPlotAreaChrome (paridade série).
 */
export function GaugeChartView({ model, options, chartParts, interaction }: Props) {
  return (
    <SeriesChartClassesProvider prefix={SERIES_CHART_PREFIX}>
      <GaugeChartViewInner
        model={model}
        options={options}
        chartParts={chartParts}
        interaction={interaction}
      />
    </SeriesChartClassesProvider>
  );
}

function GaugeChartViewInner({ model, options, chartParts, interaction }: Props) {
  const cn = useSeriesChartClasses();
  const chartArea = resolveChartAreaStyle(options, chartParts);
  const plotArea = resolvePlotAreaStyle(chartParts);
  const interactive = Boolean(interaction);
  const chartAreaRef = { kind: "chartArea" as const };
  const plotAreaRef = { kind: "plotArea" as const };
  const chartAreaSelected = isChartPartRefEqual(chartAreaRef, interaction?.selectedPart);
  const chartAreaFrame = getChartPartState(chartParts, chartAreaRef)?.frame;
  const showChartAreaResize =
    chartAreaSelected &&
    !isFullBleedChartAreaFrame(chartAreaFrame) &&
    chartPartAllowsResize(chartAreaRef) &&
    Boolean(interaction?.onPartResizePointerDown);

  const chartAreaFrameCss: CSSProperties = (() => {
    if (!chartAreaFrame || isFullBleedChartAreaFrame(chartAreaFrame)) {
      return { width: "100%", height: "100%", boxSizing: "border-box" };
    }
    const f = clampChartPartFrame(chartAreaFrame);
    return {
      position: "absolute",
      left: `${f.x}%`,
      top: `${f.y}%`,
      width: f.w != null ? `${f.w}%` : "100%",
      height: f.h != null ? `${f.h}%` : "100%",
      boxSizing: "border-box",
    };
  })();

  const shellStyle: CSSProperties = {
    ["--delpi-ui-series-chart-radius" as string]: `${chartArea.borderRadius}px`,
    ["--delpi-ui-series-chart-shadow" as string]: chartArea.boxShadow || "none",
    boxShadow: chartArea.boxShadow,
    borderRadius: chartArea.borderRadius,
  };

  const themeStyle: CSSProperties = {
    ...seriesChartThemeStyle({ ...options, backgroundColor: chartArea.fill }),
    background: chartArea.fill,
    border: `${Math.max(0, chartArea.strokeWidth)}px solid ${chartArea.stroke}`,
    borderRadius: chartArea.borderRadius,
    boxShadow: "none",
    boxSizing: "border-box",
    overflow: "visible",
    backgroundClip: "padding-box",
    display: "flex",
    flexDirection: "column",
    ...(chartArea.opacity != null ? { opacity: chartArea.opacity } : {}),
    ...chartAreaFrameCss,
  };

  const plotHostStyle: CSSProperties = {
    flex: 1,
    minHeight: 0,
    width: "100%",
    position: "relative",
    display: "flex",
    flexDirection: "column",
    alignItems: "stretch",
    justifyContent: "stretch",
    boxSizing: "border-box",
    background: plotArea.fill,
    border: `${Math.max(0, plotArea.strokeWidth)}px solid ${plotArea.stroke}`,
    borderRadius: plotArea.borderRadius,
    ...(plotArea.opacity != null ? { opacity: plotArea.opacity } : {}),
  };

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

  /* ChartContainer já aplica cn.root — aqui só âncora + modificadores. */
  const rootClass = [
    "tdp-gauge-chart",
    interactive ? `${cn.root}--interactive` : "",
    chartAreaSelected ? `${cn.root}__part--selected` : "",
  ]
    .filter(Boolean)
    .join(" ");

  const plotBody =
    model.value == null ? (
      <div className={cn.rootEmpty} style={{ display: "flex", alignItems: "center", justifyContent: "center", flex: 1 }}>
        Sem dados
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
        fillHost
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
    <div className="delpi-ui-series-chart-shell" style={shellStyle}>
      <ChartContainer
        className={rootClass}
        style={themeStyle}
        onPointerDown={onChartAreaPointerDown}
        onDoubleClick={onChartAreaDoubleClick}
        {...chartPartDomProps(chartAreaRef, interaction?.selectedPart)}
        data-chart-type="gauge"
      >
        <ChartTitle
          title={model.title}
          visible={model.showTitle}
          interaction={interactive ? interaction : null}
          chartParts={chartParts}
        />
        <div
          className={cn.plotHost}
          style={plotHostStyle}
          {...chartPartDomProps(plotAreaRef, interaction?.selectedPart)}
          onPointerDown={onPlotPointerDown}
          onDoubleClick={onPlotDoubleClick}
        >
          {plotBody}
          <ChartPlotAreaChrome
            layout={GAUGE_FULL_BLEED_PLOT_LAYOUT as import("@delpi/plugin-ui/index").SeriesChartLayout}
            interaction={interactive ? interaction : null}
            chartParts={chartParts}
          />
        </div>
        <ChartPartResizeHandles
          visible={showChartAreaResize}
          onResizePointerDown={(handle, event) => {
            interaction?.onPartResizePointerDown?.(chartAreaRef, event, handle);
          }}
        />
      </ChartContainer>
    </div>
  );
}
