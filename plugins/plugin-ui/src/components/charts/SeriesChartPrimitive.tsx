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
  SERIES_CHART_CATEGORY_PALETTE,
  type SeriesChartKind,
  type SeriesChartOptions,
  type SeriesChartPoint,
  type SeriesChartSeriesSpec,
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
  isFullBleedChartAreaFrame,
  mergeSeriesChartOptionsWithParts,
  resolveChartAreaStyle,
  resolveChartPartFontSize,
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
  /** Multi-série (overlay). Quando length > 1, o paint deve desenhar todas. */
  seriesList?: SeriesChartSeriesSpec[];
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
  /** Quando informado com 2+ itens, escala Y e legenda usam todas as séries. */
  seriesList?: SeriesChartSeriesSpec[];
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
  seriesList,
  options,
  chartParts,
  interaction,
  emptyMessage = "Sem série",
  className,
  renderPlotArea,
}: SeriesChartPrimitiveProps) {
  const cn = useSeriesChartClasses();
  const config = mergeSeriesChartOptionsWithParts(options, chartParts);
  const normalizedSeries =
    seriesList && seriesList.length > 0
      ? seriesList.map((series) => ({
          ...series,
          points: usableSeriesChartPoints(series.points),
        }))
      : undefined;
  // Multi-série: série vazia (ex.: campo fantasma «quantidade») não pode zerar o gráfico.
  const seriesWithData = normalizedSeries?.filter((series) => series.points.length > 0);
  const usable =
    seriesWithData && seriesWithData.length > 0
      ? seriesWithData[0]!.points
      : usableSeriesChartPoints(points);
  const multiSeries = Boolean(seriesWithData && seriesWithData.length > 1);
  const primarySeriesForAxis =
    seriesWithData?.filter((series) => series.plotOn !== "secondary") ?? [];
  const secondarySeriesForAxis =
    seriesWithData?.filter((series) => series.plotOn === "secondary") ?? [];
  const axisSourceSeries =
    primarySeriesForAxis.length > 0 ? primarySeriesForAxis : seriesWithData;
  const collectSeriesValues = (list: NonNullable<typeof seriesWithData>) =>
    list.flatMap((series) =>
      series.points
        .map((point) => (point.value == null ? null : Number(point.value)))
        .filter((value): value is number => value != null && Number.isFinite(value)),
    );
  const axisValues = multiSeries
    ? chartType === "stacked_bar"
      ? (() => {
          const n = Math.max(...seriesWithData!.map((series) => series.points.length), 0);
          const sums: number[] = [];
          for (let i = 0; i < n; i += 1) {
            let sum = 0;
            for (const series of seriesWithData!) {
              const raw = Number(series.points[i]?.value);
              if (Number.isFinite(raw) && raw > 0) sum += raw;
            }
            sums.push(sum);
          }
          return sums;
        })()
      : axisSourceSeries && axisSourceSeries.length > 0
        ? collectSeriesValues(axisSourceSeries)
        : undefined
    : undefined;
  const secondaryAxisValues =
    multiSeries && chartType !== "stacked_bar" && secondarySeriesForAxis.length > 0
      ? collectSeriesValues(secondarySeriesForAxis)
      : undefined;
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
    // Tipografia live no resize do bloco muda title/legend → host flex muda de altura.
  }, [usable.length, chartParts, options?.title, options?.showLegend, options?.legendPosition]);

  if (usable.length === 0) {
    const emptyArea = resolveChartAreaStyle(config, chartParts);
    return (
      <div
        className="delpi-ui-series-chart-shell"
        style={{
          ["--delpi-ui-series-chart-radius" as string]: `${emptyArea.borderRadius}px`,
          ["--delpi-ui-series-chart-shadow" as string]: emptyArea.boxShadow || "none",
          boxShadow: emptyArea.boxShadow,
          borderRadius: emptyArea.borderRadius,
        }}
      >
        <ChartContainer
          className={className}
          empty
          emptyMessage={emptyMessage}
          style={seriesChartThemeStyle(config)}
        />
      </div>
    );
  }

  const valueFormat = config.valueFormat ?? "auto";
  const plotFrame = getChartPartState(chartParts, { kind: "plotArea" })?.frame;
  const axisXFont = resolveChartPartFontSize(
    "axis",
    getChartPartState(chartParts, { kind: "axis", axis: "x" })?.style,
  );
  const axisYFont = resolveChartPartFontSize(
    "axis",
    getChartPartState(chartParts, { kind: "axis", axis: "y" })?.style,
  );
  const axisTitleXFont = resolveChartPartFontSize(
    "axisTitle",
    getChartPartState(chartParts, { kind: "axisTitle", axis: "x" })?.style,
  );
  const axisTitleYFont = resolveChartPartFontSize(
    "axisTitle",
    getChartPartState(chartParts, { kind: "axisTitle", axis: "y" })?.style,
  );
  const layout = buildSeriesChartLayout({
    points: usable,
    axisValues,
    secondaryAxisValues,
    showXAxisLabels: config.showAxes !== false && config.showXAxisLabels !== false,
    showXAxisTitle: config.showXAxisTitle !== false,
    viewW: viewSize.w,
    viewH: viewSize.h,
    categoryPaddingPercent: config.categoryPaddingPercent,
    plotFrame,
    typography: {
      axisFontSize: Math.max(axisXFont, axisYFont),
      axisTitleFontSize: Math.max(axisTitleXFont, axisTitleYFont),
    },
  });

  const seriesColor = resolveSeriesStrokeColor(config, chartParts);
  const strokeWidth = resolveSeriesStrokeWidth(chartParts);
  const chartArea = resolveChartAreaStyle(config, chartParts);
  const title = config.title?.trim();
  const seriesName = resolveSeriesName(config);
  const showLegend = config.showLegend !== false && config.legendPosition !== "hidden";
  const showAxes = config.showAxes !== false;
  const ariaLabel = title || seriesName;
  const legendItems =
    multiSeries && seriesWithData
      ? seriesWithData.map((series, index) => ({
          name: series.name,
          color:
            series.color?.trim() ||
            config.categoryColors?.[index] ||
            SERIES_CHART_CATEGORY_PALETTE[index % SERIES_CHART_CATEGORY_PALETTE.length] ||
            seriesColor,
        }))
      : undefined;
  const chartAreaRef = { kind: "chartArea" as const };
  const chartAreaSelected = isChartPartRefEqual(chartAreaRef, interaction?.selectedPart);
  const chartAreaFrame = getChartPartState(chartParts, chartAreaRef)?.frame;
  const chartAreaFrameCss: CSSProperties | undefined = (() => {
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
    // Sombra na moldura do shell (próprio box-shadow não é cortado pelo overflow:hidden).
    boxShadow: chartArea.boxShadow,
    borderRadius: chartArea.borderRadius,
  };
  const themeStyle: CSSProperties = {
    ...seriesChartThemeStyle({ ...config, backgroundColor: chartArea.fill }),
    background: chartArea.fill,
    border: `${Math.max(0, chartArea.strokeWidth)}px solid ${chartArea.stroke}`,
    borderRadius: chartArea.borderRadius,
    boxShadow: "none",
    boxSizing: "border-box",
    // Clip ao radius; com seleção do fundo libera overflow p/ handles.
    overflow: chartAreaSelected ? "visible" : "hidden",
    backgroundClip: "padding-box",
    ...(chartArea.opacity != null ? { opacity: chartArea.opacity } : {}),
    ...chartAreaFrameCss,
  };

  const plotProps: SeriesPlotRenderProps = {
    chartType,
    layout,
    config,
    points: usable,
    seriesList: seriesWithData && seriesWithData.length > 0 ? seriesWithData : normalizedSeries,
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
      items={legendItems}
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
    <div className="delpi-ui-series-chart-shell" style={shellStyle}>
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
            !isFullBleedChartAreaFrame(chartAreaFrame) &&
            chartPartAllowsResize(chartAreaRef) &&
            Boolean(interaction?.onPartResizePointerDown)
          }
          onResizePointerDown={(handle, event) =>
            interaction?.onPartResizePointerDown?.(chartAreaRef, event, handle)
          }
        />
      </ChartContainer>
    </div>
  );
}
