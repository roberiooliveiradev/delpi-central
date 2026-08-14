import { useMemo } from "react";
import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { PersistedChartType } from "../../hooks/usePersistedChartPreferences";
import { withLinearTrendField } from "../../utils/linearTrendSeries";

export type MultiTypeSeriesSpec = {
  dataKey: string;
  name: string;
  fill: string;
  /** OLS trend source (column/line/area only). */
  trendSource?: boolean;
};

export type MultiTypeSeriesChartProps = {
  data: ReadonlyArray<Record<string, unknown>>;
  categoryKey: string;
  series: ReadonlyArray<MultiTypeSeriesSpec>;
  chartType: PersistedChartType;
  height?: number;
  showTrend?: boolean;
  trendSeriesName?: string;
  formatY?: (value: number) => string;
  formatTooltipValue?: (value: number) => string;
  showLegend?: boolean;
  onCategoryClick?: (category: string) => void;
  margin?: { top?: number; right?: number; left?: number; bottom?: number };
};

const TREND_STROKE = "var(--delpi-ui-text-muted, #64748b)";

function defaultFormatY(value: number): string {
  if (!Number.isFinite(value)) return "—";
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 0 });
}

/**
 * Recharts multi-type series plot (column / line / area / pie / bar / horizontal / stacked).
 */
export function MultiTypeSeriesChart({
  data,
  categoryKey,
  series,
  chartType,
  height = 280,
  showTrend = false,
  trendSeriesName = "Tendência",
  formatY = defaultFormatY,
  formatTooltipValue,
  showLegend = true,
  onCategoryClick,
  margin = { top: 12, right: 16, left: 4, bottom: 4 },
}: MultiTypeSeriesChartProps) {
  const trendSources = useMemo(
    () => series.filter((entry) => entry.trendSource),
    [series],
  );

  const chartData = useMemo(() => {
    let rows = data.map((row) => ({ ...row }));
    const trendAllowed =
      chartType === "column" || chartType === "line" || chartType === "area";
    if (!showTrend || !trendAllowed || trendSources.length === 0) return rows;
    for (const source of trendSources) {
      rows = withLinearTrendField(rows, source.dataKey, `_trend_${source.dataKey}`);
    }
    return rows;
  }, [chartType, data, showTrend, trendSources]);

  const tooltipValue = formatTooltipValue ?? formatY;

  const formatTooltip = (value: unknown, name: unknown): [string, string] => [
    value == null || Number.isNaN(Number(value)) ? "—" : tooltipValue(Number(value)),
    String(name ?? ""),
  ];

  const handleBarCategoryClick = (bar: unknown) => {
    if (!onCategoryClick) return;
    const payload = (bar as { payload?: Record<string, unknown> } | null)?.payload;
    const category = payload?.[categoryKey];
    if (category != null) onCategoryClick(String(category));
  };

  const trendLines =
    showTrend &&
    (chartType === "column" || chartType === "line" || chartType === "area")
      ? trendSources.map((source) => (
          <Line
            key={`_trend_${source.dataKey}`}
            type="linear"
            dataKey={`_trend_${source.dataKey}`}
            name={
              trendSources.length > 1
                ? `${trendSeriesName} (${source.name})`
                : trendSeriesName
            }
            stroke={TREND_STROKE}
            strokeWidth={2}
            strokeDasharray="4 4"
            dot={false}
            connectNulls
            legendType="line"
            isAnimationActive={false}
          />
        ))
      : null;

  if (chartType === "pie") {
    const primary = series[0];
    if (!primary) return null;
    const pieData = chartData.map((row) => ({
      name: String(row[categoryKey] ?? ""),
      value: Number(row[primary.dataKey]) || 0,
      fill: primary.fill,
    }));
    return (
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Tooltip
            formatter={(value) =>
              value == null || Number.isNaN(Number(value))
                ? "—"
                : tooltipValue(Number(value))
            }
          />
          {showLegend ? <Legend /> : null}
          <Pie
            data={pieData}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={Math.min(height * 0.35, 110)}
            onClick={(entry) => {
              if (!onCategoryClick || !entry?.name) return;
              onCategoryClick(String(entry.name));
            }}
          >
            {pieData.map((entry, index) => (
              <Cell
                key={`${entry.name}-${index}`}
                fill={series[index % series.length]?.fill ?? primary.fill}
              />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
    );
  }

  if (chartType === "horizontal_bar") {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={chartData} layout="vertical" margin={margin}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
          <XAxis
            type="number"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => formatY(Number(value))}
          />
          <YAxis
            type="category"
            dataKey={categoryKey}
            width={120}
            tick={{ fontSize: 11 }}
          />
          <Tooltip
            formatter={formatTooltip}
            labelFormatter={(label) => String(label)}
          />
          {showLegend ? <Legend /> : null}
          {series.map((entry) => (
            <Bar
              key={entry.dataKey}
              dataKey={entry.dataKey}
              name={entry.name}
              fill={entry.fill}
              radius={[0, 4, 4, 0]}
              cursor={onCategoryClick ? "pointer" : undefined}
              onClick={handleBarCategoryClick}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    );
  }

  if (chartType === "line") {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData} margin={margin}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey={categoryKey}
            tick={{ fontSize: 11 }}
            interval="preserveStartEnd"
          />
          <YAxis
            width={88}
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => formatY(Number(value))}
          />
          <Tooltip
            formatter={formatTooltip}
            labelFormatter={(label) => String(label)}
          />
          {showLegend ? <Legend /> : null}
          {series.map((entry) => (
            <Line
              key={entry.dataKey}
              type="monotone"
              dataKey={entry.dataKey}
              name={entry.name}
              stroke={entry.fill}
              strokeWidth={2}
              dot={{ r: 3 }}
              connectNulls
            />
          ))}
          {trendLines}
        </LineChart>
      </ResponsiveContainer>
    );
  }

  if (chartType === "area") {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={chartData} margin={margin}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey={categoryKey}
            tick={{ fontSize: 11 }}
            interval="preserveStartEnd"
            tickLine={false}
          />
          <YAxis
            width={88}
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => formatY(Number(value))}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            formatter={formatTooltip}
            labelFormatter={(label) => String(label)}
          />
          {showLegend ? <Legend /> : null}
          {series.map((entry) => (
            <Area
              key={entry.dataKey}
              type="monotone"
              dataKey={entry.dataKey}
              name={entry.name}
              stroke={entry.fill}
              fill={entry.fill}
              fillOpacity={0.25}
              strokeWidth={2}
            />
          ))}
          {trendLines}
        </ComposedChart>
      </ResponsiveContainer>
    );
  }

  // column | bar | stacked_bar
  const stackId = chartType === "stacked_bar" ? "stack" : undefined;
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={chartData} margin={margin}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey={categoryKey}
          tick={{ fontSize: 11 }}
          interval="preserveStartEnd"
          tickLine={false}
        />
        <YAxis
          width={88}
          tick={{ fontSize: 12 }}
          tickFormatter={(value) => formatY(Number(value))}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip
            formatter={formatTooltip}
            labelFormatter={(label) => String(label)}
          />
        {showLegend ? <Legend /> : null}
        {series.map((entry) => (
          <Bar
            key={entry.dataKey}
            dataKey={entry.dataKey}
            name={entry.name}
            fill={entry.fill}
            stackId={stackId}
            radius={[4, 4, 0, 0]}
            maxBarSize={48}
            cursor={onCategoryClick ? "pointer" : undefined}
            onClick={handleBarCategoryClick}
          />
        ))}
        {trendLines}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
