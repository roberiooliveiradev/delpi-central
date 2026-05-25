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

type ChartPresentation = Extract<ChatPresentation, { type: "chart" }>;

const DEFAULT_COLORS = [
  "#0ea5e9", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444",
  "#06b6d4", "#ec4899", "#84cc16", "#f97316", "#6366f1",
];

function useIsDarkMode(): boolean {
  return useMemo(() => {
    if (typeof window === "undefined") return false;
    const root = document.documentElement;
    if (root.getAttribute("data-theme") === "dark") return true;
    if (root.getAttribute("data-theme") === "light") return false;
    return (
      root.classList.contains("dark") ||
      document.body.classList.contains("dark") ||
      window.matchMedia("(prefers-color-scheme: dark)").matches
    );
  }, []);
}

export function ChatRichChart({
  presentation,
}: {
  presentation: ChartPresentation;
}) {
  const { title, chartType, data, config } = presentation;
  const [downloadReady, setDownloadReady] = useState(false);
  const isDark = useIsDarkMode();

  const xAxis = config?.xAxis || guessXAxis(data);
  const yAxes = normalizeYAxes(config?.yAxis, data, xAxis);
  const colors = config?.colors || DEFAULT_COLORS;
  const showLegend = config?.legend !== false && yAxes.length > 1;
  const gridColor = isDark ? "#334155" : "#e2e8f0";
  const tickStyle = { fontSize: 11, fill: isDark ? "#94a3b8" : "#64748b" };
  const tooltipStyle = isDark
    ? { backgroundColor: "#1e293b", border: "1px solid #334155", color: "#e2e8f0" }
    : undefined;

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
      ctx!.fillStyle = "#ffffff";
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
  }, [title]);

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
