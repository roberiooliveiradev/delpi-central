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

type ChartPresentation = Extract<ChatPresentation, { type: "chart" }>;

export function ChatRichChart({
  presentation,
}: {
  presentation: ChartPresentation;
}) {
  const { title, chartType, data, config } = presentation;
  const [downloadReady, setDownloadReady] = useState(false);
  const isDark = useMdcDarkMode();

  const xAxis = config?.xAxis || guessXAxis(data);
  const yAxes = normalizeYAxes(config?.yAxis, data, xAxis);
  const chartTheme = useMemo(() => readMdcChartTheme(isDark), [isDark]);
  const colors = config?.colors || chartTheme.seriesColors;
  const showLegend = config?.legend !== false && yAxes.length > 1;
  const { gridColor, tickFill, tooltipStyle, exportBackground } = chartTheme;
  const tickStyle = { fontSize: 11, fill: tickFill };

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
        <span className="mdc-rich-chart__title">{title}</span>
        <div className="mdc-rich-chart__actions">
          <button
            className="mdc-rich-chart__btn"
            onClick={exportPng}
            title="Baixar PNG"
          >
            {downloadReady ? "✓ Salvo" : "↓ PNG"}
          </button>
        </div>
      </div>

      <div className="mdc-rich-chart__container">
        <ResponsiveContainer width="100%" height={280}>
          {renderChart(chartType, data, xAxis, yAxes, colors, showLegend, {
            gridColor,
            tickStyle,
            tooltipStyle,
          })}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

type ThemeConfig = {
  gridColor: string;
  tickStyle: { fontSize: number; fill: string };
  tooltipStyle?: React.CSSProperties;
};

function renderChart(
  type: string,
  data: Record<string, unknown>[],
  xAxis: string,
  yAxes: string[],
  colors: string[],
  showLegend: boolean,
  theme: ThemeConfig,
) {
  const commonProps = { data, margin: { top: 10, right: 20, left: 10, bottom: 5 } };

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
              dot={{ r: 3 }}
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
