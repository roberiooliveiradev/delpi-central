import type { CSSProperties, MouseEvent as ReactMouseEvent, PointerEvent as ReactPointerEvent } from "react";
import {
  ChartTitle,
  SeriesChartClassesProvider,
  SpeedometerGauge,
  chartPartAllowsMove,
  chartPartDomProps,
  isChartPartRefEqual,
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
 * `chartArea` usa o mesmo guard `closest` do SeriesChartPrimitive — não engole subpartes.
 */
export function GaugeChartView({ model, options, chartParts, interaction }: Props) {
  const chartArea = resolveChartAreaStyle(options, chartParts);
  const interactive = Boolean(interaction);
  const chartAreaRef = { kind: "chartArea" as const };
  const chartAreaDom = chartPartDomProps(chartAreaRef, interaction?.selectedPart);
  const chartAreaSelected = isChartPartRefEqual(chartAreaRef, interaction?.selectedPart);

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
            interaction={interactive ? interaction : null}
            chartParts={chartParts}
            aria-label={model.title || model.label}
          />
        )}
      </div>
    </SeriesChartClassesProvider>
  );
}
