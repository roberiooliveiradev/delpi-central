import {
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
  type PointerEvent as ReactPointerEvent,
} from "react";

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
  chartPartAllowsMove,
  chartPartAllowsResize,
  chartPartDomProps,
  clampChartPartFrame,
  getChartPartState,
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
  ChartPartResizeHandles,
  ChartPlotAreaChrome,
  ChartTitle,
  resolveSeriesName,
  SERIES_CHART_VIEW_H,
  SERIES_CHART_VIEW_W,
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
  const interactive = Boolean(interaction?.onPartPointerDown || interaction?.onPartDoubleClick);
  const plotHostRef = useRef<HTMLDivElement>(null);
  const [viewSize, setViewSize] = useState({ w: SERIES_CHART_VIEW_W, h: SERIES_CHART_VIEW_H });

  useLayoutEffect(() => {
    const node = plotHostRef.current;
    if (!node) return;

    const update = () => {
      const width = node.clientWidth;
      const height = node.clientHeight;
      // Host ainda medindo (0) — mantém viewBox anterior; evita “congelar” em size inválido.
      if (width < 8 || height < 8) return;
      const nextW = Math.max(width, 40);
      const nextH = Math.max(height, 40);
      setViewSize((prev) =>
        Math.abs(prev.w - nextW) < 1 && Math.abs(prev.h - nextH) < 1
          ? prev
          : { w: nextW, h: nextH },
      );
    };

    update();
    if (typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(update);
    observer.observe(node);
    return () => observer.disconnect();
  }, [usable.length]);

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
  const plotFrame = getChartPartState(chartParts, { kind: "plotArea" })?.frame;
  const layout = buildSeriesChartLayout({
    points: usable,
    showXAxisLabels: config.showAxes !== false && config.showXAxisLabels !== false,
    showXAxisTitle: config.showXAxisTitle !== false,
    viewW: viewSize.w,
    viewH: viewSize.h,
    categoryPaddingPercent: config.categoryPaddingPercent,
    plotFrame,
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
  const chartAreaFrame = getChartPartState(chartParts, chartAreaRef)?.frame;
  const chartAreaFrameCss: CSSProperties | undefined = chartAreaFrame
    ? (() => {
        const f = clampChartPartFrame(chartAreaFrame);
        return {
          position: "absolute",
          left: `${f.x}%`,
          top: `${f.y}%`,
          width: f.w != null ? `${f.w}%` : "100%",
          height: f.h != null ? `${f.h}%` : "100%",
          boxSizing: "border-box",
        };
      })()
    : undefined;
  const themeStyle: CSSProperties = {
    ...seriesChartThemeStyle({ ...config, backgroundColor: chartArea.fill }),
    background: chartArea.fill,
    border: `${Math.max(0, chartArea.strokeWidth)}px solid ${chartArea.stroke}`,
    borderRadius: chartArea.borderRadius,
    boxShadow: chartArea.boxShadow,
    boxSizing: "border-box",
    // Clip ao radius; com seleção do fundo libera overflow p/ handles.
    overflow: chartAreaSelected ? "visible" : "hidden",
    backgroundClip: "padding-box",
    ...chartAreaFrameCss,
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
        if (
          isChartPartRefEqual(chartAreaRef, interaction?.selectedPart) &&
          chartPartAllowsMove(chartAreaRef)
        ) {
          interaction?.onPartMovePointerDown?.(chartAreaRef, event);
        }
      }
    : undefined;

  const onChartAreaDoubleClick = interactive
    ? (event: React.MouseEvent<HTMLDivElement>) => {
        const host = (event.target as HTMLElement).closest("[data-chart-part]");
        const partId = host?.getAttribute("data-chart-part");
        if (partId && partId !== "chartArea") return;
        event.stopPropagation();
        event.preventDefault();
        interaction?.onPartDoubleClick?.(chartAreaRef, event);
      }
    : undefined;

  return (
    <ChartContainer
      className={rootClass}
      style={themeStyle}
      onPointerDown={onChartAreaPointerDown}
      onDoubleClick={onChartAreaDoubleClick}
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
        {config.legendPosition === "left" ? legend : null}
        <div className={cn.plotHost} ref={plotHostRef}>
          <ChartFrame viewW={layout.viewW} viewH={layout.viewH} ariaLabel={ariaLabel}>
            {renderPlotArea(plotProps)}
          </ChartFrame>
          <ChartPlotAreaChrome layout={layout} interaction={interaction} chartParts={chartParts} />
        </div>
        {config.legendPosition === "right" ? legend : null}
      </div>

      {config.legendPosition === "bottom" ? legend : null}
      <ChartDataTable
        points={usable}
        seriesName={seriesName}
        valueFormat={valueFormat}
        visible={Boolean(config.showDataTable)}
        interaction={interaction}
        chartParts={chartParts}
      />
      <ChartPartResizeHandles
        visible={
          chartAreaSelected &&
          chartPartAllowsResize(chartAreaRef) &&
          Boolean(interaction?.onPartResizePointerDown)
        }
        onResizePointerDown={(handle, event) =>
          interaction?.onPartResizePointerDown?.(chartAreaRef, event, handle)
        }
      />
    </ChartContainer>
  );
}
