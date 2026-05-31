import { useState, useCallback, useMemo } from "react";
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
import { ChatTableRowMenu } from "./ChatTableRowMenu";
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
}: {
  presentation: ChartPresentation;
  hideTitle?: boolean;
  onDrillDown?: (query: string) => void;
}) {
  const { title, chartType, data, config } = presentation;
  const [downloadReady, setDownloadReady] = useState(false);
  const [chartTypeOverride, setChartTypeOverride] = useState<string | null>(null);
  const activeChartType = chartTypeOverride || chartType;
  const [pointMenu, setPointMenu] = useState<{
    anchor: { x: number; y: number };
    actions: ReturnType<typeof buildChartPointMenuActions>;
  } | null>(null);
  const isDark = useMdcDarkMode();

  const xAxis = config?.xAxis || guessXAxis(data);
  const yAxes = normalizeYAxes(config?.yAxis, data, xAxis);
  const chartTheme = useMemo(() => readMdcChartTheme(isDark), [isDark]);
  const colors = config?.colors || chartTheme.seriesColors;
  const showLegend = config?.legend !== false && yAxes.length > 1;
  const { gridColor, tickFill, tooltipStyle, exportBackground } = chartTheme;
  const tickStyle = { fontSize: 11, fill: tickFill };

  const openPointMenu = useCallback(
    (point: Record<string, unknown>, clientX: number, clientY: number) => {
      if (!onDrillDown) {
        return;
      }

      const actions = buildChartPointMenuActions(point, xAxis);

      if (!actions.length) {
        return;
      }

      setPointMenu({
        anchor: { x: clientX, y: clientY },
        actions,
      });
    },
    [onDrillDown, xAxis],
  );

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
          <ExpandButton presentation={presentation} onDrillDown={onDrillDown} />
        </div>
      </div>

      <div
        className={`mdc-rich-chart__container${onDrillDown ? " mdc-rich-chart__container--interactive" : ""}`}
      >
        <ResponsiveContainer width="100%" height={280}>
          {renderChart(activeChartType, data, xAxis, yAxes, colors, showLegend, config, {
            gridColor,
            tickStyle,
            tooltipStyle,
          }, onDrillDown ? openPointMenu : undefined)}
        </ResponsiveContainer>
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
