import type { CSSProperties, ReactNode, PointerEvent as ReactPointerEvent } from "react";

import {
  seriesChartThemeStyle,
  usableSeriesChartPoints,
  type SeriesChartKind,
  type SeriesChartOptions,
  type SeriesChartPoint,
  type SeriesChartValueFormat,
} from "./seriesChartOptions";
import { useSeriesChartClasses } from "./seriesChartClasses";
import {
  chartPartDomProps,
  isChartPartRefEqual,
  mergeSeriesChartOptionsWithParts,
  resolveChartAreaStyle,
  resolveSeriesStrokeColor,
  resolveSeriesStrokeWidth,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "./seriesChartParts";
import {
  buildSeriesChartLayout,
  ChartContainer,
  ChartDataTable,
  ChartFrame,
  ChartLegend,
  ChartTitle,
  resolveSeriesName,
  type SeriesChartLayout,
} from "./seriesChart";

export type SeriesPlotRenderProps = {
  chartType: SeriesChartKind;
  layout: SeriesChartLayout;
  config: SeriesChartOptions;
  points: SeriesChartPoint[];
  seriesColor: string;
  valueFormat: SeriesChartValueFormat;
  showAxes: boolean;
  showGrid: boolean;
  showVerticalGrid: boolean;
  showMarkers: boolean;
  showDataLabels: boolean;
  interaction?: SeriesChartInteraction | null;
  chartParts?: ChartPartsMap | null;
  strokeWidth?: number;
};

export type SeriesChartPrimitiveProps = {
  chartType: SeriesChartKind;
  points: SeriesChartPoint[];
  options?: SeriesChartOptions | null;
  chartParts?: ChartPartsMap | null;
  interaction?: SeriesChartInteraction | null;
  emptyMessage?: string;
  className?: string;
  renderPlotArea: (props: SeriesPlotRenderProps) => ReactNode;
};

/** Gráfico de série — estrutura compartilhada (título, legenda, eixos, frame). */
export function SeriesChartPrimitive({
  chartType,
  points,
  options,
  chartParts,
  interaction,
  emptyMessage = "Sem série",
  className,
  renderPlotArea,
}: SeriesChartPrimitiveProps) {
  const cn = useSeriesChartClasses();
  const config = mergeSeriesChartOptionsWithParts(options, chartParts);
  const usable = usableSeriesChartPoints(points);
  const interactive = Boolean(interaction?.onPartPointerDown);

  if (usable.length === 0) {
    return (
      <ChartContainer
        className={className}
        empty
        emptyMessage={emptyMessage}
        style={seriesChartThemeStyle(config)}
      />
    );
  }

  const valueFormat = config.valueFormat ?? "auto";
  const layout = buildSeriesChartLayout({
    points: usable,
    showXAxisLabels: config.showAxes !== false && config.showXAxisLabels !== false,
    showXAxisTitle: config.showXAxisTitle === true,
  });

  const seriesColor = resolveSeriesStrokeColor(config, chartParts);
  const strokeWidth = resolveSeriesStrokeWidth(chartParts);
  const chartArea = resolveChartAreaStyle(config, chartParts);
  const title = config.title?.trim();
  const seriesName = resolveSeriesName(config);
  const showLegend = config.showLegend !== false && config.legendPosition !== "hidden";
  const showAxes = config.showAxes !== false;
  const ariaLabel = title || seriesName;
  const chartAreaRef = { kind: "chartArea" as const };
  const chartAreaSelected = isChartPartRefEqual(chartAreaRef, interaction?.selectedPart);
  const themeStyle: CSSProperties = {
    ...seriesChartThemeStyle({ ...config, backgroundColor: chartArea.fill }),
    background: chartArea.fill,
    border: `${Math.max(0, chartArea.strokeWidth)}px solid ${chartArea.stroke}`,
    borderRadius: chartArea.borderRadius,
    boxSizing: "border-box",
  };

  const plotProps: SeriesPlotRenderProps = {
    chartType,
    layout,
    config,
    points: usable,
    seriesColor,
    valueFormat,
    showAxes,
    showGrid: config.showGrid !== false,
    showVerticalGrid: Boolean(config.showVerticalGrid),
    showMarkers: config.showMarkers !== false,
    showDataLabels: Boolean(config.showDataLabels),
    interaction,
    chartParts,
    strokeWidth,
  };

  const legend = (
    <ChartLegend
      seriesName={seriesName}
      seriesColor={seriesColor}
      position={config.legendPosition ?? "bottom"}
      visible={showLegend}
      interaction={interaction}
      chartParts={chartParts}
    />
  );

  const rootClass =
    [
      className,
      interactive ? `${cn.root}--interactive` : "",
      chartAreaSelected ? `${cn.root}__part--selected` : "",
    ]
      .filter(Boolean)
      .join(" ") || undefined;

  const onChartAreaPointerDown = interactive
    ? (event: ReactPointerEvent<HTMLDivElement>) => {
        const host = (event.target as HTMLElement).closest("[data-chart-part]");
        const partId = host?.getAttribute("data-chart-part");
        if (partId && partId !== "chartArea") return;
        event.stopPropagation();
        interaction?.onPartPointerDown?.(chartAreaRef, event);
      }
    : undefined;

  return (
    <ChartContainer
      className={rootClass}
      style={themeStyle}
      onPointerDown={onChartAreaPointerDown}
      {...(interactive ? chartPartDomProps(chartAreaRef, interaction?.selectedPart) : {})}
    >
      <ChartTitle
        title={title}
        visible={config.showTitle !== false}
        interaction={interaction}
        chartParts={chartParts}
      />
      {config.legendPosition === "top" ? legend : null}

      <div className={cn.body}>
        <ChartFrame viewW={layout.viewW} viewH={layout.viewH} ariaLabel={ariaLabel}>
          {renderPlotArea(plotProps)}
        </ChartFrame>
        {config.legendPosition === "right" ? legend : null}
      </div>

      {config.legendPosition === "bottom" ? legend : null}
      <ChartDataTable
        points={usable}
        seriesName={seriesName}
        valueFormat={valueFormat}
        visible={Boolean(config.showDataTable)}
        interaction={interaction}
      />
    </ChartContainer>
  );
}
