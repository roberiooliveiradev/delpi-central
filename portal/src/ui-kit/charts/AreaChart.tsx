import { useId, useMemo } from "react";
import {
  Area,
  AreaChart as RechartsAreaChart,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { StableResponsiveContainer } from "./StableResponsiveContainer";
import "./AreaChart.css";

export type AreaChartPoint = {
  name: string;
  value: number;
};

export type AreaChartProps = {
  data: AreaChartPoint[];
  color?: string;
  height?: number;
  valueFormatter?: (value: number) => string;
  valueSuffix?: string;
  emptyMessage?: string;
  showHint?: boolean;
  hintText?: string;
};

const DEFAULT_HEIGHT = 260;

function defaultFormatValue(value: number): string {
  return value.toLocaleString("pt-BR");
}

type TooltipPayloadItem = {
  value?: number | string;
  color?: string;
};

type AreaChartTooltipProps = {
  active?: boolean;
  label?: string | number;
  payload?: TooltipPayloadItem[];
  formatter: (value: number) => string;
  valueSuffix?: string;
  color: string;
};

function AreaChartTooltip({
  active,
  label,
  payload,
  formatter,
  valueSuffix,
  color,
}: AreaChartTooltipProps) {
  if (!active || !payload?.length) return null;

  const value = Number(payload[0]?.value ?? 0);
  const formatted = formatter(value);
  const display = valueSuffix ? `${formatted} ${valueSuffix}` : formatted;

  return (
    <div className="portal-area-chart__tooltip" role="status">
      <p className="portal-area-chart__tooltip-label">{String(label ?? "")}</p>
      <p className="portal-area-chart__tooltip-value" style={{ color }}>
        {display}
      </p>
    </div>
  );
}

export function AreaChart({
  data,
  color = "var(--chart-1)",
  height = DEFAULT_HEIGHT,
  valueFormatter = defaultFormatValue,
  valueSuffix,
  emptyMessage = "Sem dados para exibir.",
  showHint = true,
  hintText = "Passe o mouse sobre o gráfico para ver os valores.",
}: AreaChartProps) {
  const gradientId = useId().replace(/:/g, "");
  const denseXAxis = data.length > 14;

  const axisStroke = "var(--border)";
  const tickFill = "var(--text-muted)";
  const gridStroke = "color-mix(in srgb, var(--border) 70%, transparent)";

  const chartMargin = useMemo(
    () => ({
      top: 12,
      right: 12,
      left: 4,
      bottom: denseXAxis ? 28 : 8,
    }),
    [denseXAxis],
  );

  if (data.length === 0) {
    return <p className="portal-area-chart__empty">{emptyMessage}</p>;
  }

  return (
    <div className="portal-area-chart">
      <div className="portal-area-chart__canvas" style={{ height }}>
        <StableResponsiveContainer width="100%" height={height}>
          <RechartsAreaChart data={data} margin={chartMargin}>
            <defs>
              <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0.42} />
                <stop offset="100%" stopColor={color} stopOpacity={0.04} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
            <XAxis
              dataKey="name"
              interval="preserveStartEnd"
              minTickGap={denseXAxis ? 28 : 16}
              angle={denseXAxis ? -35 : 0}
              textAnchor={denseXAxis ? "end" : "middle"}
              height={denseXAxis ? 48 : 32}
              tick={{ fontSize: 11, fill: tickFill }}
              stroke={axisStroke}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              width={52}
              tickFormatter={(value) => valueFormatter(Number(value))}
              tick={{ fontSize: 11, fill: tickFill }}
              stroke={axisStroke}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              cursor={{
                stroke: color,
                strokeWidth: 1,
                strokeDasharray: "4 4",
                strokeOpacity: 0.55,
              }}
              content={
                <AreaChartTooltip
                  formatter={valueFormatter}
                  valueSuffix={valueSuffix}
                  color={color}
                />
              }
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke={color}
              fill={`url(#${gradientId})`}
              fillOpacity={1}
              strokeWidth={2}
              isAnimationActive={false}
              activeDot={{ r: 5, strokeWidth: 2, stroke: "var(--surface-elevated, var(--surface))" }}
              dot={false}
            />
          </RechartsAreaChart>
        </StableResponsiveContainer>
      </div>
      {showHint ? <p className="portal-area-chart__hint">{hintText}</p> : null}
    </div>
  );
}
