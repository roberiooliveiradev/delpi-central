import type { CSSProperties, ReactNode } from "react";

import {
  mergeSeriesChartOptions,
  seriesChartThemeStyle,
  usableSeriesChartPoints,
  type SeriesChartKind,
  type SeriesChartOptions,
  type SeriesChartPoint,
  type SeriesChartValueFormat,
} from "./seriesChartOptions";
import { useSeriesChartClasses } from "./seriesChartClasses";
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
};

export type SeriesChartPrimitiveProps = {
  chartType: SeriesChartKind;
  points: SeriesChartPoint[];
  options?: SeriesChartOptions | null;
  emptyMessage?: string;
  className?: string;
  renderPlotArea: (props: SeriesPlotRenderProps) => ReactNode;
};

/** Gráfico de série — estrutura compartilhada (título, legenda, eixos, frame). */
export function SeriesChartPrimitive({
  chartType,
  points,
  options,
  emptyMessage = "Sem série",
  className,
  renderPlotArea,
}: SeriesChartPrimitiveProps) {
  const cn = useSeriesChartClasses();
  const config = mergeSeriesChartOptions(options);
  const usable = usableSeriesChartPoints(points);

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

  const seriesColor = config.seriesColor || "#0d7a8c";
  const title = config.title?.trim();
  const seriesName = resolveSeriesName(config);
  const showLegend = config.showLegend !== false && config.legendPosition !== "hidden";
  const showAxes = config.showAxes !== false;
  const ariaLabel = title || seriesName;
  const themeStyle = seriesChartThemeStyle(config);

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
  };

  const legend = (
    <ChartLegend
      seriesName={seriesName}
      seriesColor={seriesColor}
      position={config.legendPosition ?? "bottom"}
      visible={showLegend}
    />
  );

  return (
    <ChartContainer className={className} style={themeStyle}>
      <ChartTitle title={title} visible={config.showTitle !== false} />
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
      />
    </ChartContainer>
  );
}
