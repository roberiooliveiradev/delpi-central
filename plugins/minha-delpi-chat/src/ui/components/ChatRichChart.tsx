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
          {renderChart(chartType, data, xAxis, yAxes, colors, showLegend, {
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
  theme: ThemeConfig,
  onPointClick?: ChartPointClickHandler,
) {
  const commonProps = { data, margin: { top: 10, right: 20, left: 10, bottom: 5 } };
  const interactiveCursor = onPointClick ? "pointer" : undefined;

  switch (type) {
    case "line":
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
