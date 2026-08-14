import { useMemo } from "react";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { withLinearTrendField } from "../utils/linearTrendSeries";

export type GroupedColumnBarSpec = {
  dataKey: string;
  name: string;
  fill: string;
  trendSource?: boolean;
};

export type GroupedColumnSeriesChartProps = {
  data: ReadonlyArray<Record<string, unknown>>;
  categoryKey: string;
  bars: ReadonlyArray<GroupedColumnBarSpec>;
  height?: number;
  showTrend?: boolean;
  formatY?: (value: number) => string;
  formatTooltipValue?: (value: number) => string;
  showLegend?: boolean;
  onCategoryClick?: (category: string) => void;
  trendSeriesName?: string;
  margin?: { top?: number; right?: number; left?: number; bottom?: number };
};

const TREND_STROKE = "var(--dc-fg-muted, #64748b)";

function defaultFormatY(value: number): string {
  if (!Number.isFinite(value)) return "—";
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 0 });
}

/**
 * Local mirror of commercial GroupedColumnSeriesChart (no cross-MFE import).
 */
export function GroupedColumnSeriesChart({
  data,
  categoryKey,
  bars,
  height = 280,
  showTrend = false,
  formatY = defaultFormatY,
  formatTooltipValue,
  showLegend = true,
  onCategoryClick,
  trendSeriesName = "Tendência",
  margin = { top: 12, right: 16, left: 4, bottom: 4 },
}: GroupedColumnSeriesChartProps) {
  const trendSources = useMemo(
    () => bars.filter((bar) => bar.trendSource),
    [bars],
  );

  const chartData = useMemo(() => {
    let rows = data.map((row) => ({ ...row }));
    if (!showTrend || trendSources.length === 0) return rows;
    for (const source of trendSources) {
      const trendKey = `_trend_${source.dataKey}`;
      rows = withLinearTrendField(rows, source.dataKey, trendKey);
    }
    return rows;
  }, [data, showTrend, trendSources]);

  const tooltipValue = formatTooltipValue ?? formatY;

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
          formatter={(value, name) => [
            value == null || Number.isNaN(Number(value))
              ? "—"
              : tooltipValue(Number(value)),
            name,
          ]}
          labelFormatter={(label) => String(label)}
        />
        {showLegend ? <Legend /> : null}
        {bars.map((bar) => (
          <Bar
            key={bar.dataKey}
            dataKey={bar.dataKey}
            name={bar.name}
            fill={bar.fill}
            radius={[4, 4, 0, 0]}
            maxBarSize={48}
            cursor={onCategoryClick ? "pointer" : undefined}
            onClick={(entry) => {
              if (!onCategoryClick) return;
              const category = entry?.[categoryKey];
              if (category != null) onCategoryClick(String(category));
            }}
          />
        ))}
        {showTrend
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
          : null}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
