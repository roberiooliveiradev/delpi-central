import { LayoutPanelLeft } from "lucide-react";
import { useState, useCallback, useMemo } from "react";
import type { ChatCanvasOpenPayload } from "../../data/api/chatTypes";
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
import type { ChatPresentation } from "../../data/api/chatTypes";
import { readMdcChartTheme, useMdcDarkMode } from "../theme/mdcCssVars";
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
import { ChatTableRowMenu } from "./ChatTableRowMenu";
import { presentationToCanvasPayload } from "./chartCanvasMarkdown";
import { ExpandButton } from "./ChatExpandModal";

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

export function ChatRichChart({
  presentation,
  hideTitle = false,
  onDrillDown,
  onOpenCanvas,
}: {
  presentation: ChartPresentation;
  hideTitle?: boolean;
  onDrillDown?: (query: string) => void;
  onOpenCanvas?: (payload: ChatCanvasOpenPayload) => void;
}) {
  const { title, chartType, data, config } = presentation;
  const [downloadReady, setDownloadReady] = useState(false);
  const [chartTypeOverride, setChartTypeOverride] = useState<string | null>(null);
  const [topFilter, setTopFilter] = useState<ChartTopFilter>("all");
  const [zoomWindow, setZoomWindow] = useState<ChartZoomWindow>("all");
  const [periodCompareEnabled, setPeriodCompareEnabled] = useState(false);
  const activeChartType = chartTypeOverride || chartType;
  const [pointMenu, setPointMenu] = useState<{
    anchor: { x: number; y: number };
    actions: ReturnType<typeof buildChartPointMenuActions>;
  } | null>(null);
  const isDark = useMdcDarkMode();

  const xAxis = config?.xAxis || guessXAxis(data);
  const baseYAxes = normalizeYAxes(config?.yAxis, data, xAxis);
  const valueKey = firstNumericValueKey(data, xAxis, baseYAxes);
  const temporalAxis = useMemo(
    () => isTemporalChartAxis(xAxis, data),
    [data, xAxis],
  );
  const periodCompareSpec = useMemo(
    () => detectPeriodCompare(data, xAxis, valueKey),
    [data, valueKey, xAxis],
  );

  const chartView = useMemo(() => {
    let rows = [...data];
    let axes = [...baseYAxes];
    let axisKey = xAxis;

    if (periodCompareEnabled && periodCompareSpec) {
      const compared = buildPeriodComparisonRows(rows, periodCompareSpec);

      rows = compared.rows;
      axes = compared.yAxes;
      axisKey = periodCompareSpec.categoryKey;
    } else {
      rows = applyChartTopFilter(rows, axisKey, valueKey, topFilter);

      if (temporalAxis) {
        rows = applyChartZoomWindow(rows, zoomWindow);
      }
    }

    return { rows, axes, axisKey };
  }, [
    baseYAxes,
    data,
    periodCompareEnabled,
    periodCompareSpec,
    temporalAxis,
    topFilter,
    valueKey,
    xAxis,
    zoomWindow,
  ]);

  const displayData = chartView.rows;
  const displayYAxes = chartView.axes;
  const displayXAxis = chartView.axisKey;

  const chartTheme = useMemo(() => readMdcChartTheme(isDark), [isDark]);
  const colors = config?.colors || chartTheme.seriesColors;
  const showLegend = config?.legend !== false && displayYAxes.length > 1;
  const { gridColor, tickFill, tooltipStyle, exportBackground } = chartTheme;
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
        anchor: { x: clientX, y: clientY },
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

    return parts.length ? parts.join(" · ") : undefined;
  }, [
    chartTypeOverride,
    periodCompareEnabled,
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
    const svg = document.querySelector(".mdc-rich-chart__container svg");
    if (!svg) return;

    const svgData = new XMLSerializer().serializeToString(svg);
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    const img = new Image();

    img.onload = () => {
      canvas.width = img.width * 2;
      canvas.height = img.height * 2;
      ctx!.scale(2, 2);
      ctx!.fillStyle = exportBackground;
      ctx!.fillRect(0, 0, canvas.width, canvas.height);
      ctx!.drawImage(img, 0, 0);

      const a = document.createElement("a");
      a.download = `${title || "grafico"}.png`;
      a.href = canvas.toDataURL("image/png");
      a.click();
      setDownloadReady(true);
      setTimeout(() => setDownloadReady(false), 2000);
    };

    img.src = "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(svgData)));
  }, [exportBackground, title]);

  return (
    <div className="mdc-rich-chart">
      <div className="mdc-rich-chart__header">
        {hideTitle ? (
          <span className="mdc-rich-chart__title" aria-hidden="true" />
        ) : (
          <span className="mdc-rich-chart__title">{title}</span>
        )}
        <div className="mdc-rich-chart__actions">
          {data.length > 0 && activeChartType !== "heatmap" ? (
            <div className="mdc-rich-chart__ux-toolbar" role="group" aria-label="Filtros do gráfico">
              {!periodCompareEnabled ? (
                <label className="mdc-rich-chart__ux-field">
                  <span>Top</span>
                  <select
                    value={topFilter}
                    onChange={(event) =>
                      setTopFilter(event.target.value as ChartTopFilter)
                    }
                  >
                    <option value="all">Todos</option>
                    <option value="5">5</option>
                    <option value="10">10</option>
                    <option value="20">20</option>
                  </select>
                </label>
              ) : null}
              {temporalAxis && !periodCompareEnabled ? (
                <label className="mdc-rich-chart__ux-field">
                  <span>Janela</span>
                  <select
                    value={zoomWindow}
                    onChange={(event) =>
                      setZoomWindow(event.target.value as ChartZoomWindow)
                    }
                  >
                    <option value="all">Tudo</option>
                    <option value="6">6</option>
                    <option value="12">12</option>
                    <option value="24">24</option>
                  </select>
                </label>
              ) : null}
              {periodCompareSpec ? (
                <label className="mdc-rich-chart__ux-toggle">
                  <input
                    type="checkbox"
                    checked={periodCompareEnabled}
                    onChange={(event) => {
                      const enabled = event.target.checked;
                      setPeriodCompareEnabled(enabled);

                      if (enabled) {
                        setChartTypeOverride("grouped_bar");
                      }
                    }}
                  />
                  <span>Comparar períodos</span>
                </label>
              ) : null}
            </div>
          ) : null}
          {data.length > 0 ? (
            <div
              className="mdc-rich-presentation__format-toggle mdc-rich-chart__type-toggle"
              role="group"
              aria-label="Tipo de gráfico"
            >
              {CHART_TYPE_ALTERNATES.map((token) => (
                <button
                  key={token}
                  type="button"
                  className={`mdc-rich-chart__toggle-btn${activeChartType === token ? " mdc-rich-chart__toggle-btn--active" : ""}`}
                  onClick={() =>
                    setChartTypeOverride((current) => (current === token ? null : token))
                  }
                  title={CHART_TYPE_LABELS[token] ?? token}
                >
                  {CHART_TYPE_LABELS[token] ?? token}
                </button>
              ))}
            </div>
          ) : null}
          <button
            className="mdc-rich-chart__btn"
            onClick={exportPng}
            title="Baixar PNG"
          >
            {downloadReady ? "✓ Salvo" : "↓ PNG"}
          </button>
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
          <ExpandButton presentation={presentation} onDrillDown={onDrillDown} />
        </div>
      </div>

      <div
        className={`mdc-rich-chart__container${onDrillDown ? " mdc-rich-chart__container--interactive" : ""}`}
      >
        {activeChartType === "heatmap" ? (
          <HeatmapGrid
            data={displayData}
            xAxis={config?.xAxis || displayXAxis}
            yAxis={
              typeof config?.yAxis === "string"
                ? config.yAxis
                : Array.isArray(config?.yAxis)
                  ? String(config.yAxis[0] || guessXAxis(data))
                  : guessYAxisCategory(data, xAxis)
            }
            valueKey={config?.valueKey || displayYAxes[0] || "value"}
            colors={colors}
            tickFill={tickFill}
            onPointClick={onDrillDown ? openPointMenu : undefined}
          />
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            {renderChart(activeChartType, displayData, displayXAxis, displayYAxes, colors, showLegend, config, {
              gridColor,
              tickStyle,
              tooltipStyle,
            }, onDrillDown ? openPointMenu : undefined)}
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
) {
  const commonProps = { data, margin: { top: 10, right: 20, left: 10, bottom: 5 } };
  const interactiveCursor = onPointClick ? "pointer" : undefined;

  switch (type) {
    case "line":
    case "multi_line":
      return (
        <LineChart {...commonProps}>
          <CartesianGrid strokeDasharray="3 3" stroke={theme.gridColor} />
          <XAxis dataKey={xAxis} tick={theme.tickStyle} />
          <YAxis tick={theme.tickStyle} />
          <Tooltip contentStyle={theme.tooltipStyle} />
          {showLegend && <Legend />}
          {yAxes.map((key, i) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={colors[i % colors.length]}
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
          <XAxis dataKey={xAxis} tick={theme.tickStyle} />
          <YAxis tick={theme.tickStyle} />
          <Tooltip contentStyle={theme.tooltipStyle} />
          {showLegend && <Legend />}
          {yAxes.map((key, i) => (
            <Area
              key={key}
              type="monotone"
              dataKey={key}
              stroke={colors[i % colors.length]}
              fill={colors[i % colors.length]}
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
              <Cell key={i} fill={colors[i % colors.length]} />
            ))}
          </Pie>
        </PieChart>
      );

    case "horizontal_bar":
      return (
        <BarChart {...commonProps} layout="vertical" margin={{ top: 10, right: 20, left: 8, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={theme.gridColor} />
          <XAxis type="number" tick={theme.tickStyle} />
          <YAxis type="category" dataKey={xAxis} width={120} tick={theme.tickStyle} />
          <Tooltip contentStyle={theme.tooltipStyle} />
          {showLegend && <Legend />}
          {yAxes.map((key, i) => (
            <Bar
              key={key}
              dataKey={key}
              fill={colors[i % colors.length]}
              radius={[0, 4, 4, 0]}
              cursor={interactiveCursor}
              onClick={(bar, _index, event) => {
                chartPointFromEvent(bar, event, onPointClick);
              }}
            />
          ))}
        </BarChart>
      );

    case "combo": {
      const barKey = chartConfig?.comboBarKey || yAxes[0];
      const lineKey = chartConfig?.comboLineKey || yAxes[1] || yAxes[0];

      return (
        <ComposedChart {...commonProps}>
          <CartesianGrid strokeDasharray="3 3" stroke={theme.gridColor} />
          <XAxis dataKey={xAxis} tick={theme.tickStyle} />
          <YAxis tick={theme.tickStyle} />
          <Tooltip contentStyle={theme.tooltipStyle} />
          {showLegend && <Legend />}
          {barKey ? (
            <Bar
              dataKey={barKey}
              fill={colors[0]}
              radius={[4, 4, 0, 0]}
              cursor={interactiveCursor}
            />
          ) : null}
          {lineKey ? (
            <Line
              type="monotone"
              dataKey={lineKey}
              stroke={colors[1 % colors.length]}
              strokeWidth={2}
              dot={{ r: 3, cursor: interactiveCursor }}
            />
          ) : null}
        </ComposedChart>
      );
    }

    case "scatter": {
      const scatterX = chartConfig?.xAxis || yAxes[0] || xAxis;
      const scatterY = yAxes[0] || "value";

      return (
        <ScatterChart {...commonProps}>
          <CartesianGrid strokeDasharray="3 3" stroke={theme.gridColor} />
          <XAxis type="number" dataKey={scatterX} tick={theme.tickStyle} name={scatterX} />
          <YAxis type="number" dataKey={scatterY} tick={theme.tickStyle} name={scatterY} />
          <Tooltip contentStyle={theme.tooltipStyle} />
          {showLegend && <Legend />}
          <Scatter
            name="Dados"
            data={data}
            fill={colors[0]}
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
          <XAxis dataKey={xAxis} tick={theme.tickStyle} />
          <YAxis tick={theme.tickStyle} />
          <Tooltip contentStyle={theme.tooltipStyle} />
          {showLegend && <Legend />}
          {yAxes.map((key, i) => (
            <Bar
              key={key}
              dataKey={key}
              stackId="stack"
              fill={colors[i % colors.length]}
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
      const gaugeData = [{ name: "Atual", value: fill, fill: colors[0] }];

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
          <XAxis dataKey={xAxis} tick={theme.tickStyle} />
          <YAxis tick={theme.tickStyle} />
          <Tooltip contentStyle={theme.tooltipStyle} />
          {showLegend && <Legend />}
          {yAxes.map((key, i) => (
            <Bar
              key={key}
              dataKey={key}
              fill={colors[i % colors.length]}
              radius={[4, 4, 0, 0]}
              cursor={interactiveCursor}
              onClick={(bar, _index, event) => {
                chartPointFromEvent(bar, event, onPointClick);
              }}
            />
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

function guessYAxisCategory(data: Record<string, unknown>[], xAxis: string): string {
  if (!data.length) return "category";

  const first = data[0];
  const stringKeys = Object.keys(first).filter(
    (key) => typeof first[key] === "string" && key !== xAxis,
  );

  return stringKeys[0] || "category";
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

  const ratio = Math.min(1, Math.max(0, (value - min) / (max - min)));
  return `color-mix(in srgb, ${lowColor} ${Math.round((1 - ratio) * 100)}%, ${highColor})`;
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

  const lowColor = colors[0] || "#93c5fd";
  const highColor = colors[1] || colors[0] || "#1d4ed8";

  return (
    <div className="mdc-heatmap" role="img" aria-label="Mapa de calor">
      <div
        className="mdc-heatmap__grid"
        style={{
          gridTemplateColumns: `minmax(5rem, auto) repeat(${xLabels.length}, minmax(2.5rem, 1fr))`,
        }}
      >
        <div className="mdc-heatmap__corner" />
        {xLabels.map((label) => (
          <div key={label} className="mdc-heatmap__x-label" style={{ color: tickFill }}>
            {label}
          </div>
        ))}
        {yLabels.map((yLabel) => (
          <div key={yLabel} className="mdc-heatmap__row">
            <div className="mdc-heatmap__y-label" style={{ color: tickFill }}>
              {yLabel}
            </div>
            {xLabels.map((xLabel) => {
              const value = valueMap.get(`${yLabel}\u0000${xLabel}`);
              const hasValue = value !== undefined;
              const background = hasValue
                ? heatColor(value, min, max, lowColor, highColor)
                : "transparent";

              return (
                <div
                  key={`${yLabel}-${xLabel}`}
                  className={`mdc-heatmap__cell${hasValue ? " mdc-heatmap__cell--filled" : ""}`}
                  style={{ background }}
                  title={hasValue ? `${yLabel} × ${xLabel}: ${value}` : undefined}
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
        <span className="mdc-heatmap__legend-bar" />
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
