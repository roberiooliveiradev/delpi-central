import { LayoutPanelLeft } from "lucide-react";
import { useState, useCallback, useMemo, useRef, useEffect } from "react";
import { NativeCheckboxControl } from "@delpi/plugin-ui/index";
import type { ChatCanvasOpenPayload } from "../../../data/api/chatTypes";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  AreaChart,
  Area,
  ComposedChart,
  ScatterChart,
  Scatter,
  RadialBarChart,
  RadialBar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { ChatPresentation } from "../../../data/api/chatTypes";
import {
  readMdcChartTheme,
  resolveChartSeriesColor,
  resolveChartSeriesColors,
  useMdcDarkMode,
} from "../../theme/mdcCssVars";
import { buildChartPointMenuActions } from "./chatDrillDown";
import {
  applyChartTopFilter,
  applyChartZoomWindow,
  buildPeriodComparisonRows,
  detectPeriodCompare,
  firstNumericValueKey,
  isTemporalChartAxis,
  type ChartTopFilter,
  type ChartZoomWindow,
} from "./chartPresentationUx";
import { aggregateChartRowsByCategory } from "./pipeline/chartCategoryAggregation";
import { ChatTableRowMenu } from "../shared/menus/ChatTableRowMenu";
import { presentationToCanvasPayload } from "./export/chartCanvasMarkdown";
import { exportChartElementToPng } from "./export/chartPngExport";
import { ChatPresentationExportButtons } from "./ChatPresentationExportButtons";
import {
  formatChartColumnLabel,
  inferDefaultChartAxes,
  isNumericAxisChartType,
} from "./pipeline/chartAxisSelection";
import {
  formatChartAxisValue,
  type FieldFormats,
  type FieldLabels,
} from "./pipeline/presentationFieldLabels";
import { ChatMarkdown } from "../message/ChatMarkdown";
import { ExpandButton } from "../canvas/ChatExpandModal";
import type { ChartViewState } from "./chartViewState";
import { recordPresentationTelemetry } from "./pipeline/presentationTelemetry";
import {
  applyCategoryFilter,
  buildCategoryFilterOptions,
} from "./pipeline/presentationCategoryFilter";
import { normalizeChartPresentation } from "./pipeline/chartPresentationNormalize";
import { ChatRichUxSelect } from "./chatRichUxSelect";
import { ChatRichSearchField } from "./ChatRichSearchField";
import { richPresentationToolbar } from "../../../content/presentationVocabulary";
import "./ChatRichSearchField.css";

type ChartPresentation = Extract<ChatPresentation, { type: "chart" }>;

const CHART_TYPE_LABELS: Record<string, string> = {
  bar: "Barras",
  line: "Linhas",
  area: "Área",
  horizontal_bar: "H. barras",
  donut: "Rosca",
  pie: "Pizza",
  grouped_bar: "Agrupado",
  stacked_bar: "Empilhado",
  multi_line: "Multi-linha",
  combo: "Combo",
  scatter: "Dispersão",
  histogram: "Histograma",
  gauge: "Gauge",
  heatmap: "Mapa de calor",
};

const CHART_TYPE_ALTERNATES = [
  "bar",
  "line",
  "area",
  "horizontal_bar",
  "donut",
  "pie",
  "combo",
  "scatter",
  "histogram",
] as const;

function chartTypeAlternatesFor(sourceChartType: string): string[] {
  if (sourceChartType === "heatmap") {
    return ["heatmap", ...CHART_TYPE_ALTERNATES];
  }
  return [...CHART_TYPE_ALTERNATES];
}

function resolveCartesianYAxes(args: {
  scatterMode: boolean;
  resolvedY: string;
  axisYOverride: string | null;
  configYAxis: string | string[] | undefined;
  valueKeyFromConfig: string;
  sourceChartType: string;
  activeChartType: string;
  filteredData: Record<string, unknown>[];
  xAxis: string;
}): string[] {
  const {
    scatterMode,
    resolvedY,
    axisYOverride,
    configYAxis,
    valueKeyFromConfig,
    sourceChartType,
    activeChartType,
    filteredData,
    xAxis,
  } = args;
  if (scatterMode) {
    return [resolvedY].filter(Boolean);
  }
  if (axisYOverride) {
    return normalizeYAxes([axisYOverride], filteredData, xAxis);
  }
  // Heatmap config.yAxis is a categorical matrix dimension — never use it as a numeric series.
  if (valueKeyFromConfig && (sourceChartType === "heatmap" || activeChartType !== "heatmap")) {
    if (sourceChartType === "heatmap" && activeChartType !== "heatmap") {
      return normalizeYAxes([valueKeyFromConfig], filteredData, xAxis);
    }
    if (activeChartType !== "heatmap" && valueKeyFromConfig) {
      const sample = filteredData[0]?.[valueKeyFromConfig];
      if (typeof sample === "number" && Number.isFinite(sample)) {
        return normalizeYAxes([valueKeyFromConfig], filteredData, xAxis);
      }
    }
  }
  return normalizeYAxes(configYAxis, filteredData, xAxis);
}

export function ChatRichChart({
  presentation,
  hideTitle = false,
  hideToolbar = false,
  expanded = false,
  initialViewState,
  chartExplanation,
  showExplanation = false,
  onShowExplanationChange,
  onDrillDown,
  onOpenCanvas,
}: {
  presentation: ChartPresentation;
  hideTitle?: boolean;
  /** Oculta toolbar (legado). No modal expandido use `expanded` para manter os controles. */
  hideToolbar?: boolean;
  expanded?: boolean;
  initialViewState?: ChartViewState;
  chartExplanation?: string;
  showExplanation?: boolean;
  onShowExplanationChange?: (open: boolean) => void;
  onDrillDown?: (query: string) => void;
  onOpenCanvas?: (payload: ChatCanvasOpenPayload) => void;
}) {
  const normalizedPresentation = normalizeChartPresentation(presentation) ?? presentation;
  const { title, chartType, data: rawData, config } = normalizedPresentation;
  const data = Array.isArray(rawData) ? rawData : [];
  const [downloadReady, setDownloadReady] = useState(false);
  const [chartTypeOverride, setChartTypeOverride] = useState<string | null>(
    initialViewState?.chartTypeOverride ?? null,
  );
  const [axisXOverride, setAxisXOverride] = useState<string | null>(
    initialViewState?.axisXOverride ?? null,
  );
  const [axisYOverride, setAxisYOverride] = useState<string | null>(
    initialViewState?.axisYOverride ?? null,
  );
  const [valueKeyOverride, setValueKeyOverride] = useState<string | null>(
    initialViewState?.valueKeyOverride ?? null,
  );
  const [categoryFilterKey, setCategoryFilterKey] = useState<string | null>(
    initialViewState?.categoryFilterKey ?? null,
  );
  const [categoryFilterValue, setCategoryFilterValue] = useState<string | null>(
    initialViewState?.categoryFilterValue ?? null,
  );
  const [topFilter, setTopFilter] = useState<ChartTopFilter>(
    initialViewState?.topFilter ?? "all",
  );
  const [zoomWindow, setZoomWindow] = useState<ChartZoomWindow>(
    initialViewState?.zoomWindow ?? "all",
  );
  const [periodCompareEnabled, setPeriodCompareEnabled] = useState(
    initialViewState?.periodCompareEnabled ?? false,
  );
  const activeChartType = chartTypeOverride || chartType;
  const isHeatmapActive = activeChartType === "heatmap";
  const configuredValueKey =
    typeof config?.valueKey === "string" ? config.valueKey.trim() : "";
  const typeAlternates = useMemo(
    () => chartTypeAlternatesFor(chartType),
    [chartType],
  );
  const displayTitle = useMemo(() => {
    if (!chartTypeOverride || chartTypeOverride === chartType) {
      return title;
    }
    return CHART_TYPE_LABELS[activeChartType] ?? title;
  }, [activeChartType, chartType, chartTypeOverride, title]);
  const skipAxisResetOnMountRef = useRef(Boolean(initialViewState));

  useEffect(() => {
    if (skipAxisResetOnMountRef.current) {
      skipAxisResetOnMountRef.current = false;
      return;
    }

    setChartTypeOverride(null);
    setAxisXOverride(null);
    setAxisYOverride(null);
    setValueKeyOverride(null);
    setCategoryFilterKey(null);
    setCategoryFilterValue(null);
    setTopFilter("all");
    setZoomWindow("all");
    setPeriodCompareEnabled(false);
  }, [data, title, chartType]);

  const [pointMenu, setPointMenu] = useState<{
    anchor: { point: { x: number; y: number } };
    actions: ReturnType<typeof buildChartPointMenuActions>;
  } | null>(null);
  const isDark = useMdcDarkMode();
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const fieldLabels = config?.fieldLabels;
  const fieldFormats = config?.fieldFormats;

  const categoryFilterOptions = useMemo(
    () =>
      buildCategoryFilterOptions(
        data,
        config?.categoryColumns?.length ? config.categoryColumns : undefined,
        fieldLabels,
      ),
    [config?.categoryColumns, data, fieldLabels],
  );

  const activeCategoryFilterOption = useMemo(
    () => categoryFilterOptions.find((option) => option.key === categoryFilterKey) ?? null,
    [categoryFilterKey, categoryFilterOptions],
  );

  const filteredData = useMemo(
    () =>
      applyCategoryFilter(
        data,
        categoryFilterKey,
        categoryFilterValue,
        activeCategoryFilterOption?.mode ?? "equality",
      ),
    [activeCategoryFilterOption?.mode, categoryFilterKey, categoryFilterValue, data],
  );

  const axisDefaults = useMemo(
    () => inferDefaultChartAxes(filteredData, activeChartType, config),
    [activeChartType, config, filteredData],
  );

  const scatterMode = isNumericAxisChartType(activeChartType);
  const resolvedX = axisXOverride ?? axisDefaults.xKey;
  const resolvedY = axisYOverride ?? axisDefaults.yKey;
  const xAxis = scatterMode ? resolvedX : resolvedX || config?.xAxis || guessXAxis(filteredData);
  const baseYAxes = resolveCartesianYAxes({
    scatterMode,
    resolvedY,
    axisYOverride,
    configYAxis: config?.yAxis,
    valueKeyFromConfig: configuredValueKey,
    sourceChartType: chartType,
    activeChartType,
    filteredData,
    xAxis,
  });
  const valueKey = isHeatmapActive
    ? valueKeyOverride ||
      configuredValueKey ||
      firstNumericValueKey(filteredData, xAxis, baseYAxes)
    : firstNumericValueKey(filteredData, xAxis, baseYAxes);
  const temporalAxis = useMemo(
    () => isTemporalChartAxis(xAxis, filteredData),
    [filteredData, xAxis],
  );
  const periodCompareSpec = useMemo(
    () => detectPeriodCompare(filteredData, xAxis, valueKey),
    [filteredData, valueKey, xAxis],
  );

  const chartView = useMemo(() => {
    let rows = [...filteredData];
    let axes = [...baseYAxes];
    let axisKey = xAxis;

    if (periodCompareEnabled && periodCompareSpec) {
      const compared = buildPeriodComparisonRows(rows, periodCompareSpec);

      rows = compared.rows;
      axes = compared.yAxes;
      axisKey = periodCompareSpec.categoryKey;
    } else {
      // Heatmap matrix must keep both categorical axes + valueKey; category aggregation
      // would collapse rows and empty the grid.
      if (!scatterMode && axisKey && !isHeatmapActive) {
        rows = aggregateChartRowsByCategory(rows, axisKey, axes);
      }

      if (!isHeatmapActive) {
        rows = applyChartTopFilter(rows, axisKey, valueKey, topFilter);
      }

      if (temporalAxis && !isHeatmapActive) {
        rows = applyChartZoomWindow(rows, zoomWindow);
      }
    }

    return { rows, axes, axisKey };
  }, [
    baseYAxes,
    filteredData,
    isHeatmapActive,
    periodCompareEnabled,
    periodCompareSpec,
    temporalAxis,
    scatterMode,
    topFilter,
    valueKey,
    xAxis,
    zoomWindow,
  ]);

  const displayData = chartView.rows;
  const displayYAxes = chartView.axes;
  const displayXAxis = chartView.axisKey;

  const chartTheme = useMemo(() => readMdcChartTheme(isDark), [isDark]);
  const colors = useMemo(
    () => resolveChartSeriesColors(config?.colors, isDark, config?.paletteFamily),
    [config?.colors, config?.paletteFamily, isDark],
  );
  const showLegend = config?.legend !== false && displayYAxes.length > 1;
  const { gridColor, tickFill, tooltipStyle } = chartTheme;
  const tickStyle = { fontSize: 11, fill: tickFill };

  const openPointMenu = useCallback(
    (point: Record<string, unknown>, clientX: number, clientY: number) => {
      if (!onDrillDown) {
        return;
      }

      const actions = buildChartPointMenuActions(point, displayXAxis);

      if (!actions.length) {
        return;
      }

      setPointMenu({
        anchor: { point: { x: clientX, y: clientY } },
        actions,
      });
    },
    [displayXAxis, onDrillDown],
  );

  const filtersNote = useMemo(() => {
    const parts: string[] = [];

    if (topFilter !== "all") {
      parts.push(`Top ${topFilter}`);
    }

    if (temporalAxis && zoomWindow !== "all") {
      parts.push(`Janela ${zoomWindow} pontos`);
    }

    if (periodCompareEnabled) {
      parts.push("Comparar períodos");
    }

    if (chartTypeOverride) {
      parts.push(`Visualização ${CHART_TYPE_LABELS[chartTypeOverride] ?? chartTypeOverride}`);
    }

    if (axisXOverride || axisYOverride) {
      parts.push(
        `Eixos: ${formatChartColumnLabel(resolvedX, fieldLabels)} × ${formatChartColumnLabel(resolvedY, fieldLabels)}`,
      );
    }

    if (categoryFilterKey && categoryFilterValue) {
      parts.push(
        `Filtro: ${formatChartColumnLabel(categoryFilterKey, fieldLabels)} = ${categoryFilterValue}`,
      );
    }

    return parts.length ? parts.join(" · ") : undefined;
  }, [
    axisXOverride,
    axisYOverride,
    categoryFilterKey,
    categoryFilterValue,
    chartTypeOverride,
    fieldLabels,
    periodCompareEnabled,
    resolvedX,
    resolvedY,
    temporalAxis,
    topFilter,
    zoomWindow,
  ]);

  const openOnCanvas = useCallback(() => {
    if (!onOpenCanvas || displayData.length === 0) {
      return;
    }

    onOpenCanvas(
      presentationToCanvasPayload(presentation, {
        rows: displayData,
        xAxis: displayXAxis,
        yAxes: displayYAxes,
        chartType: activeChartType,
        filtersNote,
      }),
    );
  }, [
    activeChartType,
    displayData,
    displayXAxis,
    displayYAxes,
    filtersNote,
    onOpenCanvas,
    presentation,
  ]);

  const exportPng = useCallback(() => {
    exportChartElementToPng(chartContainerRef.current, title || "grafico");
    recordPresentationTelemetry("presentation_chart_export_png", {
      chartType: activeChartType,
      title: title || undefined,
    });
    setDownloadReady(true);
    setTimeout(() => setDownloadReady(false), 2000);
  }, [activeChartType, title]);

  const chartViewState = useMemo<ChartViewState>(
    () => ({
      chartTypeOverride,
      axisXOverride,
      axisYOverride,
      valueKeyOverride,
      categoryFilterKey,
      categoryFilterValue,
      topFilter,
      zoomWindow,
      periodCompareEnabled,
    }),
    [
      axisXOverride,
      axisYOverride,
      valueKeyOverride,
      categoryFilterKey,
      categoryFilterValue,
      chartTypeOverride,
      periodCompareEnabled,
      topFilter,
      zoomWindow,
    ],
  );

  const configuredHeatmapY =
    typeof config?.yAxis === "string"
      ? config.yAxis
      : Array.isArray(config?.yAxis)
        ? String(config.yAxis[0] || "")
        : "";
  const compiledBinding =
    String(config?.bindingProvenance || "")
      .trim()
      .toUpperCase() === "COMPILED";
  const heatmapXAxis =
    (isHeatmapActive ? axisXOverride : null) ||
    config?.xAxis ||
    displayXAxis ||
    guessXAxis(data);
  const guessedHeatmapY = guessYAxisCategory(data, heatmapXAxis);
  const configuredYIsUseful =
    Boolean(configuredHeatmapY) &&
    configuredHeatmapY !== heatmapXAxis &&
    categoryCardinality(data, configuredHeatmapY) > 1;
  const heatmapYAxis =
    (isHeatmapActive ? axisYOverride : null) ||
    (compiledBinding && configuredHeatmapY ? configuredHeatmapY : null) ||
    (configuredYIsUseful ? configuredHeatmapY : null) ||
    guessedHeatmapY;
  const heatmapValueKey =
    valueKeyOverride || configuredValueKey || valueKey || "value";
  const heatmapCategoryOptions = useMemo(() => {
    const keys = new Set<string>([
      ...axisDefaults.categoryColumns,
      ...(config?.xAxis ? [config.xAxis] : []),
      ...(configuredHeatmapY ? [configuredHeatmapY] : []),
      ...(heatmapXAxis ? [heatmapXAxis] : []),
      ...(heatmapYAxis ? [heatmapYAxis] : []),
    ]);
    return [...keys].filter(Boolean);
  }, [
    axisDefaults.categoryColumns,
    config?.xAxis,
    configuredHeatmapY,
    heatmapXAxis,
    heatmapYAxis,
  ]);
  const heatmapValueOptions = useMemo(() => {
    const keys = new Set<string>([
      ...axisDefaults.numericColumns,
      ...(configuredValueKey ? [configuredValueKey] : []),
      ...(heatmapValueKey ? [heatmapValueKey] : []),
    ]);
    return [...keys].filter(Boolean);
  }, [axisDefaults.numericColumns, configuredValueKey, heatmapValueKey]);
  const heatmapYOptions = useMemo(
    () =>
      heatmapCategoryOptions.filter(
        (column) => column !== heatmapXAxis || column === heatmapYAxis,
      ),
    [heatmapCategoryOptions, heatmapXAxis, heatmapYAxis],
  );

  const showToolbar = !hideToolbar || expanded;

  return (
    <div
      className={[
        "mdc-rich-chart",
        expanded ? "mdc-rich-chart--expanded" : "",
        hideToolbar && !expanded ? "mdc-rich-chart--embedded" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {showToolbar ? (
      <div className="mdc-rich-chart__header">
        {hideTitle ? (
          <span className="mdc-rich-chart__title" aria-hidden="true" />
        ) : (
          <span className="mdc-rich-chart__title">{displayTitle}</span>
        )}
        <div className="mdc-rich-chart__toolbar">
          <div className="mdc-rich-chart__toolbar-row mdc-rich-chart__toolbar-row--controls">
            {data.length > 0 && isHeatmapActive ? (
              <div
                className="mdc-rich-chart__ux-toolbar"
                role="group"
                aria-label="Parâmetros do mapa de calor"
              >
                {heatmapCategoryOptions.length > 0 ? (
                  <ChatRichUxSelect
                    label="Colunas"
                    title="Categoria no eixo horizontal"
                    value={heatmapXAxis}
                    allowEmptyOption={false}
                    onChange={(column) => {
                      setAxisXOverride(column);
                      recordPresentationTelemetry("presentation_axis_change", {
                        axis: "heatmap_x",
                        column,
                        chartType: activeChartType,
                      });
                    }}
                    options={heatmapCategoryOptions.map((column) => ({
                      value: column,
                      label: formatChartColumnLabel(column, fieldLabels),
                    }))}
                  />
                ) : null}
                {heatmapYOptions.length > 0 ? (
                  <ChatRichUxSelect
                    label="Linhas"
                    title="Categoria no eixo vertical"
                    value={heatmapYAxis}
                    allowEmptyOption={false}
                    onChange={(column) => {
                      setAxisYOverride(column);
                      recordPresentationTelemetry("presentation_axis_change", {
                        axis: "heatmap_y",
                        column,
                        chartType: activeChartType,
                      });
                    }}
                    options={heatmapYOptions.map((column) => ({
                      value: column,
                      label: formatChartColumnLabel(column, fieldLabels),
                    }))}
                  />
                ) : null}
                {heatmapValueOptions.length > 0 ? (
                  <ChatRichUxSelect
                    label="Valor"
                    title="Métrica numérica das células"
                    value={heatmapValueKey}
                    allowEmptyOption={false}
                    onChange={(column) => {
                      setValueKeyOverride(column);
                      recordPresentationTelemetry("presentation_axis_change", {
                        axis: "heatmap_value",
                        column,
                        chartType: activeChartType,
                      });
                    }}
                    options={heatmapValueOptions.map((column) => ({
                      value: column,
                      label: formatChartColumnLabel(column, fieldLabels),
                    }))}
                  />
                ) : null}
              </div>
            ) : null}
            {data.length > 0 && !isHeatmapActive ? (
              <div className="mdc-rich-chart__ux-toolbar" role="group" aria-label="Filtros do gráfico">
                {axisDefaults.numericColumns.length > 0 ? (
                  <ChatRichUxSelect
                    label="Eixo Y"
                    title="Valor numérico no eixo vertical"
                    value={resolvedY}
                    allowEmptyOption={false}
                    onChange={(column) => {
                      setAxisYOverride(column);
                      recordPresentationTelemetry("presentation_axis_change", {
                        axis: "y",
                        column,
                        chartType: activeChartType,
                      });
                    }}
                    options={axisDefaults.numericColumns.map((column) => ({
                      value: column,
                      label: formatChartColumnLabel(column, fieldLabels),
                    }))}
                  />
                ) : null}
                {(scatterMode
                  ? axisDefaults.numericColumns
                  : axisDefaults.categoryColumns
                ).length > 0 ? (
                  <ChatRichUxSelect
                    label={scatterMode ? "Eixo X" : "Categoria"}
                    title={
                      scatterMode
                        ? "Valor numérico no eixo horizontal"
                        : "Campo exibido no eixo horizontal"
                    }
                    value={resolvedX}
                    allowEmptyOption={false}
                    onChange={(column) => {
                      setAxisXOverride(column);
                      recordPresentationTelemetry("presentation_axis_change", {
                        axis: scatterMode ? "x" : "category",
                        column,
                        chartType: activeChartType,
                      });
                    }}
                    options={(scatterMode
                      ? axisDefaults.numericColumns
                      : axisDefaults.categoryColumns
                    ).map((column) => ({
                      value: column,
                      label: formatChartColumnLabel(column, fieldLabels),
                    }))}
                  />
                ) : null}
                {categoryFilterOptions.length > 0 ? (
                  <>
                    <ChatRichUxSelect
                      label={richPresentationToolbar().filterColumnLabel}
                      title="Coluna para filtrar os dados"
                      value={categoryFilterKey ?? ""}
                      onChange={(key) => {
                        setCategoryFilterKey(key || null);
                        setCategoryFilterValue(null);
                      }}
                      options={categoryFilterOptions.map((option) => ({
                        value: option.key,
                        label: option.label,
                      }))}
                    />
                    {categoryFilterKey && activeCategoryFilterOption?.mode === "contains" ? (
                      <ChatRichSearchField
                        label={richPresentationToolbar().filterContainsLabel}
                        onChange={(value) => {
                          setCategoryFilterValue(value || null);
                          if (value) {
                            recordPresentationTelemetry("presentation_category_filter", {
                              filterKey: categoryFilterKey,
                              filterValue: value,
                              chartType: activeChartType,
                              mode: "contains",
                            });
                          }
                        }}
                        placeholder={richPresentationToolbar().filterContainsPlaceholder}
                        value={categoryFilterValue ?? ""}
                      />
                    ) : null}
                    {categoryFilterKey && activeCategoryFilterOption?.mode === "equality" ? (
                      <ChatRichUxSelect
                        label={richPresentationToolbar().filterValueLabel}
                        title="Valor do filtro"
                        value={categoryFilterValue ?? ""}
                        onChange={(value) => {
                          setCategoryFilterValue(value || null);
                          if (value) {
                            recordPresentationTelemetry("presentation_category_filter", {
                              filterKey: categoryFilterKey,
                              filterValue: value,
                              chartType: activeChartType,
                              mode: "equality",
                            });
                          }
                        }}
                        options={
                          activeCategoryFilterOption.values.map((value) => ({
                            value,
                            label: value,
                          })) ?? []
                        }
                      />
                    ) : null}
                  </>
                ) : null}
                {!periodCompareEnabled ? (
                  <ChatRichUxSelect
                    label="Top"
                    value={topFilter}
                    allowEmptyOption={false}
                    onChange={(value) => setTopFilter(value as ChartTopFilter)}
                    options={[
                      { value: "all", label: "Todos" },
                      { value: "5", label: "5" },
                      { value: "10", label: "10" },
                      { value: "20", label: "20" },
                    ]}
                  />
                ) : null}
                {temporalAxis && !periodCompareEnabled ? (
                  <ChatRichUxSelect
                    label="Janela"
                    value={zoomWindow}
                    allowEmptyOption={false}
                    onChange={(value) => setZoomWindow(value as ChartZoomWindow)}
                    options={[
                      { value: "all", label: "Tudo" },
                      { value: "6", label: "6" },
                      { value: "12", label: "12" },
                      { value: "24", label: "24" },
                    ]}
                  />
                ) : null}
                {periodCompareSpec ? (
                  <NativeCheckboxControl
                    className="mdc-rich-chart__ux-toggle"
                    checked={periodCompareEnabled}
                    label="Comparar períodos"
                    onChange={(enabled) => {
                        setPeriodCompareEnabled(enabled);

                        if (enabled) {
                          setChartTypeOverride("grouped_bar");
                        }
                      }}
                  />
                ) : null}
              </div>
            ) : null}
            <div className="mdc-rich-chart__command-group" role="group" aria-label="Ações do gráfico">
              {chartExplanation ? (
                <button
                  type="button"
                  className={`mdc-rich-chart__btn${showExplanation ? " mdc-rich-chart__toggle-btn--active" : ""}`}
                  onClick={() => onShowExplanationChange?.(!showExplanation)}
                  title="Explicar como ler este gráfico"
                  aria-expanded={showExplanation}
                >
                  Explicar
                </button>
              ) : null}
              <button
                className="mdc-rich-chart__btn"
                onClick={exportPng}
                title="Baixar PNG"
                type="button"
              >
                {downloadReady ? "✓ Salvo" : "↓ PNG"}
              </button>
              <ChatPresentationExportButtons
                presentation={normalizedPresentation}
                buttonClassName="mdc-rich-chart__btn"
                getChartRoot={() => chartContainerRef.current}
              />
              {onOpenCanvas ? (
                <button
                  type="button"
                  className="mdc-rich-chart__btn"
                  onClick={openOnCanvas}
                  title="Salvar na lousa"
                >
                  <LayoutPanelLeft size={14} aria-hidden="true" />
                  Lousa
                </button>
              ) : null}
              {!expanded ? (
                <ExpandButton
                  presentation={presentation}
                  chartViewState={chartViewState}
                  onDrillDown={onDrillDown}
                  onOpenCanvas={onOpenCanvas}
                />
              ) : null}
            </div>
          </div>
          {data.length > 0 ? (
            <div className="mdc-rich-chart__toolbar-row mdc-rich-chart__toolbar-row--types">
              <div
                className="mdc-rich-chart__type-toggle"
                role="group"
                aria-label="Tipo de gráfico"
              >
                {typeAlternates.map((token) => (
                  <button
                    key={token}
                    type="button"
                    className={`mdc-rich-chart__toggle-btn${activeChartType === token ? " mdc-rich-chart__toggle-btn--active" : ""}`}
                    onClick={() => {
                      setChartTypeOverride((current) => {
                        const next = current === token ? null : token;
                        const fromType = current ?? chartType;
                        const toType = next ?? chartType;

                        if (
                          fromType === "heatmap" &&
                          toType !== "heatmap" &&
                          configuredValueKey
                        ) {
                          setAxisYOverride(configuredValueKey);
                          setValueKeyOverride(null);
                        }
                        if (toType === "heatmap") {
                          setAxisYOverride(null);
                          setValueKeyOverride(null);
                        }

                        recordPresentationTelemetry("presentation_chart_type_switch", {
                          from: fromType,
                          to: toType,
                        });

                        return next;
                      });
                    }}
                    title={CHART_TYPE_LABELS[token] ?? token}
                  >
                    {CHART_TYPE_LABELS[token] ?? token}
                  </button>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>
      ) : null}

      {showExplanation && chartExplanation ? (
        <div
          className="mdc-rich-chart__explanation"
          role="region"
          aria-label="Explicação do gráfico"
        >
          <ChatMarkdown content={chartExplanation} />
        </div>
      ) : null}

      <div
        ref={chartContainerRef}
        className={`mdc-rich-chart__container${onDrillDown ? " mdc-rich-chart__container--interactive" : ""}`}
      >
        {isHeatmapActive ? (
          <HeatmapGrid
            data={displayData}
            xAxis={heatmapXAxis}
            yAxis={heatmapYAxis}
            valueKey={heatmapValueKey}
            colors={colors}
            tickFill={tickFill}
            onPointClick={onDrillDown ? openPointMenu : undefined}
          />
        ) : (
          <ResponsiveContainer width="100%" height={expanded ? 420 : 280}>
            {renderChart(
              activeChartType,
              displayData,
              displayXAxis,
              displayYAxes,
              colors,
              showLegend,
              config,
              {
                gridColor,
                tickStyle,
                tooltipStyle,
              },
              onDrillDown ? openPointMenu : undefined,
              fieldLabels,
              fieldFormats,
              isDark,
            )}
          </ResponsiveContainer>
        )}
      </div>

      {pointMenu && onDrillDown ? (
        <ChatTableRowMenu
          actions={pointMenu.actions}
          anchor={pointMenu.anchor}
          menuLabel="Ações do ponto"
          onSelect={onDrillDown}
          onClose={() => setPointMenu(null)}
        />
      ) : null}
    </div>
  );
}

type ThemeConfig = {
  gridColor: string;
  tickStyle: { fontSize: number; fill: string };
  tooltipStyle?: React.CSSProperties;
};

type ChartPointClickHandler = (
  point: Record<string, unknown>,
  clientX: number,
  clientY: number,
) => void;

function chartPayloadFromSlice(
  slice: unknown,
): Record<string, unknown> | undefined {
  if (!slice || typeof slice !== "object") {
    return undefined;
  }

  const record = slice as Record<string, unknown>;
  const nested = record.payload;

  if (nested && typeof nested === "object") {
    return nested as Record<string, unknown>;
  }

  return record;
}

function chartPointFromEvent(
  slice: unknown,
  event: { clientX?: number; clientY?: number } | undefined,
  onPointClick?: ChartPointClickHandler,
) {
  const point = chartPayloadFromSlice(slice);

  if (!onPointClick || !point) {
    return;
  }

  onPointClick(point, event?.clientX ?? 0, event?.clientY ?? 0);
}

function buildAxisTickFormatter(
  axisKey: string,
  fieldFormats?: FieldFormats | null,
) {
  return (value: unknown) => formatChartAxisValue(value, axisKey, fieldFormats);
}

function seriesLabel(key: string, fieldLabels?: FieldLabels | null) {
  return formatChartColumnLabel(key, fieldLabels);
}

function renderBarCategoryCells(
  data: Record<string, unknown>[],
  colors: string[],
  seriesIndex: number,
  isDark: boolean,
  multiColorPerCategory: boolean,
) {
  if (!multiColorPerCategory || data.length <= 1) {
    return null;
  }

  return data.map((_, dataIndex) => (
    <Cell
      key={`bar-cell-${seriesIndex}-${dataIndex}`}
      fill={resolveChartSeriesColor(colors, dataIndex, isDark)}
    />
  ));
}

function renderChart(
  type: string,
  data: Record<string, unknown>[],
  xAxis: string,
  yAxes: string[],
  colors: string[],
  showLegend: boolean,
  chartConfig: ChartPresentation["config"],
  theme: ThemeConfig,
  onPointClick?: ChartPointClickHandler,
  fieldLabels?: FieldLabels | null,
  fieldFormats?: FieldFormats | null,
  isDark = false,
) {
  const multiColorBars = yAxes.length === 1;
  const commonProps = { data, margin: { top: 10, right: 20, left: 10, bottom: 5 } };
  const interactiveCursor = onPointClick ? "pointer" : undefined;
  const xAxisTickFormatter = buildAxisTickFormatter(xAxis, fieldFormats);

  switch (type) {
    case "line":
    case "multi_line":
      return (
        <LineChart {...commonProps}>
          <CartesianGrid strokeDasharray="3 3" stroke={theme.gridColor} />
          <XAxis dataKey={xAxis} tick={theme.tickStyle} tickFormatter={xAxisTickFormatter} />
          <YAxis tick={theme.tickStyle} />
          <Tooltip contentStyle={theme.tooltipStyle} />
          {showLegend && <Legend />}
          {yAxes.map((key, i) => (
            <Line
              key={key}
              name={seriesLabel(key, fieldLabels)}
              type="monotone"
              dataKey={key}
              stroke={resolveChartSeriesColor(colors, i, isDark)}
              strokeWidth={2}
              dot={{ r: 3, cursor: interactiveCursor }}
              activeDot={{
                r: 5,
                cursor: interactiveCursor,
                onClick: (dot, event) => {
                  chartPointFromEvent(dot, event, onPointClick);
                },
              }}
            />
          ))}
        </LineChart>
      );

    case "area":
      return (
        <AreaChart {...commonProps}>
          <CartesianGrid strokeDasharray="3 3" stroke={theme.gridColor} />
          <XAxis dataKey={xAxis} tick={theme.tickStyle} tickFormatter={xAxisTickFormatter} />
          <YAxis tick={theme.tickStyle} />
          <Tooltip contentStyle={theme.tooltipStyle} />
          {showLegend && <Legend />}
          {yAxes.map((key, i) => (
            <Area
              key={key}
              name={seriesLabel(key, fieldLabels)}
              type="monotone"
              dataKey={key}
              stroke={resolveChartSeriesColor(colors, i, isDark)}
              fill={resolveChartSeriesColor(colors, i, isDark)}
              fillOpacity={0.2}
              activeDot={{
                r: 5,
                cursor: interactiveCursor,
                onClick: (dot, event) => {
                  chartPointFromEvent(dot, event, onPointClick);
                },
              }}
            />
          ))}
        </AreaChart>
      );

    case "pie":
    case "donut":
      return (
        <PieChart>
          <Tooltip contentStyle={theme.tooltipStyle} />
          {showLegend && <Legend />}
          <Pie
            data={data}
            dataKey={yAxes[0] || "value"}
            nameKey={xAxis}
            cx="50%"
            cy="50%"
            innerRadius={type === "donut" ? 52 : 0}
            outerRadius={100}
            cursor={interactiveCursor}
            onClick={(slice, _index, event) => {
              chartPointFromEvent(slice, event, onPointClick);
            }}
            label={({ name, percent }) =>
              `${name}: ${(percent * 100).toFixed(0)}%`
            }
            labelLine={false}
          >
            {data.map((_, i) => (
              <Cell key={i} fill={resolveChartSeriesColor(colors, i, isDark)} />
            ))}
          </Pie>
        </PieChart>
      );

    case "horizontal_bar":
      return (
        <BarChart {...commonProps} layout="vertical" margin={{ top: 10, right: 20, left: 8, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={theme.gridColor} />
          <XAxis type="number" tick={theme.tickStyle} />
          <YAxis
            type="category"
            dataKey={xAxis}
            width={120}
            tick={theme.tickStyle}
            tickFormatter={xAxisTickFormatter}
          />
          <Tooltip contentStyle={theme.tooltipStyle} />
          {showLegend && <Legend />}
          {yAxes.map((key, i) => (
            <Bar
              key={key}
              name={seriesLabel(key, fieldLabels)}
              dataKey={key}
              fill={resolveChartSeriesColor(colors, i, isDark)}
              radius={[0, 4, 4, 0]}
              cursor={interactiveCursor}
              onClick={(bar, _index, event) => {
                chartPointFromEvent(bar, event, onPointClick);
              }}
            >
              {renderBarCategoryCells(data, colors, i, isDark, multiColorBars)}
            </Bar>
          ))}
        </BarChart>
      );

    case "combo": {
      const barKey = chartConfig?.comboBarKey || yAxes[0];
      const lineKey = chartConfig?.comboLineKey || yAxes[1] || yAxes[0];

      return (
        <ComposedChart {...commonProps}>
          <CartesianGrid strokeDasharray="3 3" stroke={theme.gridColor} />
          <XAxis dataKey={xAxis} tick={theme.tickStyle} tickFormatter={xAxisTickFormatter} />
          <YAxis tick={theme.tickStyle} />
          <Tooltip contentStyle={theme.tooltipStyle} />
          {showLegend && <Legend />}
          {barKey ? (
            <Bar
              name={seriesLabel(barKey, fieldLabels)}
              dataKey={barKey}
              fill={resolveChartSeriesColor(colors, 0, isDark)}
              radius={[4, 4, 0, 0]}
              cursor={interactiveCursor}
            >
              {renderBarCategoryCells(data, colors, 0, isDark, multiColorBars)}
            </Bar>
          ) : null}
          {lineKey ? (
            <Line
              name={seriesLabel(lineKey, fieldLabels)}
              type="monotone"
              dataKey={lineKey}
              stroke={resolveChartSeriesColor(colors, 1, isDark)}
              strokeWidth={2}
              dot={{ r: 3, cursor: interactiveCursor }}
            />
          ) : null}
        </ComposedChart>
      );
    }

    case "scatter": {
      const scatterX = xAxis;
      const scatterY = yAxes[0] || "value";

      return (
        <ScatterChart {...commonProps}>
          <CartesianGrid strokeDasharray="3 3" stroke={theme.gridColor} />
          <XAxis
            type="number"
            dataKey={scatterX}
            tick={theme.tickStyle}
            name={seriesLabel(scatterX, fieldLabels)}
          />
          <YAxis
            type="number"
            dataKey={scatterY}
            tick={theme.tickStyle}
            name={seriesLabel(scatterY, fieldLabels)}
          />
          <Tooltip contentStyle={theme.tooltipStyle} />
          {showLegend && <Legend />}
          <Scatter
            name="Dados"
            data={data}
            fill={resolveChartSeriesColor(colors, 0, isDark)}
            cursor={interactiveCursor}
            onClick={(point, _index, event) => {
              chartPointFromEvent(point, event, onPointClick);
            }}
          />
        </ScatterChart>
      );
    }

    case "histogram":
    case "stacked_bar":
      return (
        <BarChart {...commonProps}>
          <CartesianGrid strokeDasharray="3 3" stroke={theme.gridColor} />
          <XAxis dataKey={xAxis} tick={theme.tickStyle} tickFormatter={xAxisTickFormatter} />
          <YAxis tick={theme.tickStyle} />
          <Tooltip contentStyle={theme.tooltipStyle} />
          {showLegend && <Legend />}
          {yAxes.map((key, i) => (
            <Bar
              key={key}
              name={seriesLabel(key, fieldLabels)}
              dataKey={key}
              stackId="stack"
              fill={resolveChartSeriesColor(colors, i, isDark)}
              radius={i === yAxes.length - 1 ? [4, 4, 0, 0] : [0, 0, 0, 0]}
              cursor={interactiveCursor}
              onClick={(bar, _index, event) => {
                chartPointFromEvent(bar, event, onPointClick);
              }}
            />
          ))}
        </BarChart>
      );

    case "gauge": {
      const valueKey = chartConfig?.gaugeValueKey || yAxes[0];
      const targetKey = chartConfig?.gaugeTargetKey || yAxes[1];
      const row = data[0] ?? {};
      const rawValue = Number(row[valueKey] ?? 0);
      const rawTarget = Number(row[targetKey ?? ""] ?? rawValue);
      const maxValue = rawTarget > 0 ? rawTarget : Math.max(rawValue, 1);
      const fill = Math.min(100, Math.round((rawValue / maxValue) * 100));
      const gaugeData = [
        { name: "Atual", value: fill, fill: resolveChartSeriesColor(colors, 0, isDark) },
      ];

      return (
        <RadialBarChart
          cx="50%"
          cy="50%"
          innerRadius="58%"
          outerRadius="100%"
          barSize={18}
          data={gaugeData}
          startAngle={180}
          endAngle={0}
        >
          <RadialBar dataKey="value" cornerRadius={6} background />
          <Tooltip contentStyle={theme.tooltipStyle} />
          <Legend />
        </RadialBarChart>
      );
    }

    case "grouped_bar":
    default:
      return (
        <BarChart {...commonProps}>
          <CartesianGrid strokeDasharray="3 3" stroke={theme.gridColor} />
          <XAxis dataKey={xAxis} tick={theme.tickStyle} tickFormatter={xAxisTickFormatter} />
          <YAxis tick={theme.tickStyle} />
          <Tooltip contentStyle={theme.tooltipStyle} />
          {showLegend && <Legend />}
          {yAxes.map((key, i) => (
            <Bar
              key={key}
              name={seriesLabel(key, fieldLabels)}
              dataKey={key}
              fill={resolveChartSeriesColor(colors, i, isDark)}
              radius={[4, 4, 0, 0]}
              cursor={interactiveCursor}
              onClick={(bar, _index, event) => {
                chartPointFromEvent(bar, event, onPointClick);
              }}
            >
              {renderBarCategoryCells(data, colors, i, isDark, multiColorBars)}
            </Bar>
          ))}
        </BarChart>
      );
  }
}

function guessXAxis(data: Record<string, unknown>[]): string {
  if (!data.length) return "name";
  const first = data[0];
  const stringKeys = Object.keys(first).filter(
    (k) => typeof first[k] === "string",
  );
  return stringKeys[0] || Object.keys(first)[0] || "name";
}

function categoryCardinality(data: Record<string, unknown>[], key: string): number {
  if (!key || !data.length) return 0;

  return new Set(
    data.map((row) => String(row[key] ?? "").trim()).filter(Boolean),
  ).size;
}

function guessYAxisCategory(data: Record<string, unknown>[], xAxis: string): string {
  if (!data.length) return "category";

  const first = data[0];
  const stringKeys = Object.keys(first).filter(
    (key) => typeof first[key] === "string" && key !== xAxis,
  );

  if (!stringKeys.length) return "category";

  let bestKey = stringKeys[0];
  let bestScore = -1;

  for (const key of stringKeys) {
    const unique = categoryCardinality(data, key);
    // Colunas de unidade (ex.: "UN") têm cardinalidade 1 e não formam matriz útil.
    const score = unique <= 1 ? 0 : unique;
    if (score > bestScore) {
      bestScore = score;
      bestKey = key;
    }
  }

  return bestKey;
}

function heatIntensityRatio(value: number, min: number, max: number): number {
  if (!Number.isFinite(value) || max <= min) {
    return 1;
  }

  return Math.min(1, Math.max(0, (value - min) / (max - min)));
}

function heatColor(
  value: number,
  min: number,
  max: number,
  lowColor: string,
  highColor: string,
): string {
  if (!Number.isFinite(value)) {
    return lowColor;
  }

  if (max <= min) {
    return highColor;
  }

  const ratio = heatIntensityRatio(value, min, max);
  return `color-mix(in srgb, ${lowColor} ${Math.round((1 - ratio) * 100)}%, ${highColor})`;
}

function heatCellInk(ratio: number, isDark: boolean): string {
  if (isDark) {
    return ratio >= 0.42 ? "var(--mdc-heatmap-ink-on-high)" : "var(--mdc-heatmap-ink-on-low)";
  }

  return ratio >= 0.55 ? "var(--mdc-heatmap-ink-on-high)" : "var(--mdc-heatmap-ink-on-low)";
}

function HeatmapGrid({
  data,
  xAxis,
  yAxis,
  valueKey,
  colors,
  tickFill,
  onPointClick,
}: {
  data: Record<string, unknown>[];
  xAxis: string;
  yAxis: string;
  valueKey: string;
  colors: string[];
  tickFill: string;
  onPointClick?: ChartPointClickHandler;
}) {
  const isDark = useMdcDarkMode();
  const xLabels = useMemo(
    () => [...new Set(data.map((row) => String(row[xAxis] ?? "")))].filter(Boolean),
    [data, xAxis],
  );
  const yLabels = useMemo(
    () => [...new Set(data.map((row) => String(row[yAxis] ?? "")))].filter(Boolean),
    [data, yAxis],
  );

  const { valueMap, min, max } = useMemo(() => {
    const map = new Map<string, number>();
    let localMin = Infinity;
    let localMax = -Infinity;

    for (const row of data) {
      const raw = Number(row[valueKey]);
      const x = String(row[xAxis] ?? "");
      const y = String(row[yAxis] ?? "");

      if (!x || !y || !Number.isFinite(raw)) {
        continue;
      }

      map.set(`${y}\u0000${x}`, raw);
      localMin = Math.min(localMin, raw);
      localMax = Math.max(localMax, raw);
    }

    return {
      valueMap: map,
      min: Number.isFinite(localMin) ? localMin : 0,
      max: Number.isFinite(localMax) ? localMax : 0,
    };
  }, [data, xAxis, yAxis, valueKey]);

  const configuredLow = typeof colors[0] === "string" ? colors[0].trim() : "";
  const configuredHigh = typeof colors[1] === "string" ? colors[1].trim() : "";
  const lowColor = configuredLow || "var(--mdc-heatmap-low)";
  const highColor = configuredHigh || configuredLow || "var(--mdc-heatmap-high)";
  const denseColumns = xLabels.length >= 8;
  const singleRow = yLabels.length <= 1;

  return (
    <div
      className={`mdc-heatmap${denseColumns ? " mdc-heatmap--dense" : ""}${singleRow ? " mdc-heatmap--single-row" : ""}`}
      role="img"
      aria-label="Mapa de calor"
    >
      <div
        className="mdc-heatmap__grid"
        style={{
          gridTemplateColumns: `minmax(4.5rem, auto) repeat(${Math.max(xLabels.length, 1)}, minmax(${denseColumns ? "2.1rem" : "2.75rem"}, 1fr))`,
        }}
      >
        <div className="mdc-heatmap__corner" />
        {xLabels.map((label) => (
          <div key={label} className="mdc-heatmap__x-label" style={{ color: tickFill }} title={label}>
            {label}
          </div>
        ))}
        {yLabels.map((yLabel) => (
          <div key={yLabel} className="mdc-heatmap__row">
            <div className="mdc-heatmap__y-label" style={{ color: tickFill }} title={yLabel}>
              {yLabel}
            </div>
            {xLabels.map((xLabel) => {
              const value = valueMap.get(`${yLabel}\u0000${xLabel}`);
              const hasValue = value !== undefined;
              const ratio = hasValue ? heatIntensityRatio(value, min, max) : 0;
              const background = hasValue
                ? heatColor(value, min, max, lowColor, highColor)
                : undefined;
              const ink = hasValue ? heatCellInk(ratio, isDark) : undefined;

              return (
                <div
                  key={`${yLabel}-${xLabel}`}
                  className={`mdc-heatmap__cell${hasValue ? " mdc-heatmap__cell--filled" : " mdc-heatmap__cell--empty"}`}
                  style={{ background, color: ink }}
                  title={hasValue ? `${yLabel} × ${xLabel}: ${formatHeatValue(value)}` : undefined}
                  onClick={(event) => {
                    if (!onPointClick || !hasValue) {
                      return;
                    }

                    onPointClick(
                      { [xAxis]: xLabel, [yAxis]: yLabel, [valueKey]: value },
                      event.clientX,
                      event.clientY,
                    );
                  }}
                >
                  {hasValue ? formatHeatValue(value) : ""}
                </div>
              );
            })}
          </div>
        ))}
      </div>
      <div className="mdc-heatmap__legend" aria-hidden="true">
        <span>{formatHeatValue(min)}</span>
        <span
          className="mdc-heatmap__legend-bar"
          style={{
            background: `linear-gradient(90deg, ${lowColor} 0%, ${highColor} 100%)`,
          }}
        />
        <span>{formatHeatValue(max)}</span>
      </div>
    </div>
  );
}

function formatHeatValue(value: number): string {
  if (Math.abs(value) >= 1000) {
    return value.toLocaleString("pt-BR", { maximumFractionDigits: 0 });
  }

  return value.toLocaleString("pt-BR", { maximumFractionDigits: 1 });
}

function normalizeYAxes(
  yAxis: string | string[] | undefined,
  data: Record<string, unknown>[],
  xAxis: string,
): string[] {
  if (Array.isArray(yAxis)) return yAxis;
  if (typeof yAxis === "string") return [yAxis];
  if (!data.length) return ["value"];

  const first = data[0];
  return Object.keys(first).filter(
    (k) => k !== xAxis && typeof first[k] === "number",
  );
}
