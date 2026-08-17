import { useId, useMemo } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { delpiUiClass } from "../../utils/delpiUiClass";
import { useDelpiDarkMode } from "../bpmn/hooks/useDelpiDarkMode";
import { StableResponsiveContainer } from "./StableResponsiveContainer";

export type ComparativeAreaChartSeries = {
  dataKey: string;
  name: string;
  color: string;
  fillOpacity?: number;
};

export type ComparativeAreaChartPoint = {
  name: string;
  [key: string]: string | number | null | undefined;
};

export type ComparativeAreaChartProps = {
  data: ComparativeAreaChartPoint[];
  series: ComparativeAreaChartSeries[];
  /** Altura do plot (px). Default 240. */
  height?: number;
  valueFormatter?: (value: number) => string;
  emptyMessage?: string;
  className?: string;
  /** Prefixo BEM dual-class. Default: `ds`. */
  prefix?: string;
  yAxisWidth?: number;
  /** Gradiente suave (monotone). Default true. */
  smooth?: boolean;
};

const DEFAULT_HEIGHT = 240;

export function comparativeAreaChartBemClasses(prefix: string) {
  const ui = "delpi-ui-comparative-area-chart";
  return {
    root: delpiUiClass(`${prefix}-comparative-area-chart`, ui),
    empty: delpiUiClass(`${prefix}-comparative-area-chart__empty`, `${ui}__empty`),
    canvas: delpiUiClass(`${prefix}-comparative-area-chart__canvas`, `${ui}__canvas`),
    tooltip: delpiUiClass(`${prefix}-comparative-area-chart__tooltip`, `${ui}__tooltip`),
    tooltipLabel: delpiUiClass(
      `${prefix}-comparative-area-chart__tooltip-label`,
      `${ui}__tooltip-label`,
    ),
    tooltipRow: delpiUiClass(
      `${prefix}-comparative-area-chart__tooltip-row`,
      `${ui}__tooltip-row`,
    ),
  };
}

function defaultFormat(value: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 2,
  }).format(value);
}

type TooltipPayloadItem = {
  name?: string;
  value?: number | string;
  color?: string;
  dataKey?: string | number;
};

type CustomTooltipProps = {
  active?: boolean;
  label?: string | number;
  payload?: TooltipPayloadItem[];
  formatter: (value: number) => string;
  classNames: ReturnType<typeof comparativeAreaChartBemClasses>;
};

function ComparativeTooltip({
  active,
  label,
  payload,
  formatter,
  classNames,
}: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className={classNames.tooltip} role="status">
      <p className={classNames.tooltipLabel}>{String(label ?? "")}</p>
      {payload.map((item) => {
        const value = Number(item.value ?? 0);
        return (
          <p
            key={String(item.dataKey ?? item.name)}
            className={classNames.tooltipRow}
            style={{ color: item.color }}
          >
            {item.name}: {formatter(value)}
          </p>
        );
      })}
    </div>
  );
}

/**
 * Gráfico de área comparativo (Recharts) — padrão Transformômetro
 * (economia vs investimento / ganhos vs investimento).
 *
 * Tema claro/escuro via `useDelpiDarkMode` + tokens `--delpi-ui-*` do dashboard.
 */
export function ComparativeAreaChart({
  data,
  series,
  height = DEFAULT_HEIGHT,
  valueFormatter = defaultFormat,
  emptyMessage,
  className,
  prefix = "ds",
  yAxisWidth = 72,
  smooth = true,
}: ComparativeAreaChartProps) {
  const isDark = useDelpiDarkMode();
  const gradientId = useId().replace(/:/g, "");
  const cn = comparativeAreaChartBemClasses(prefix);
  const rootClass = [cn.root, className].filter(Boolean).join(" ");

  const axisStroke = "var(--delpi-ui-border, var(--border, #e2e8f0))";
  const tickFill = "var(--delpi-ui-muted, var(--text-muted, #64748b))";
  const gridStroke = isDark
    ? "color-mix(in srgb, var(--delpi-ui-border, #334155) 70%, transparent)"
    : "color-mix(in srgb, var(--delpi-ui-border, #e2e8f0) 85%, transparent)";

  const gradients = useMemo(
    () =>
      series.map((item) => ({
        id: `${gradientId}-${item.dataKey}`,
        color: item.color,
        opacity: item.fillOpacity ?? 0.45,
      })),
    [series, gradientId],
  );

  if (!data.length) {
    return emptyMessage ? <p className={cn.empty}>{emptyMessage}</p> : null;
  }

  return (
    <div className={rootClass} data-theme={isDark ? "dark" : "light"}>
      <div className={cn.canvas} style={{ height }}>
        <StableResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <defs>
              {gradients.map((g) => (
                <linearGradient key={g.id} id={g.id} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={g.color} stopOpacity={g.opacity} />
                  <stop offset="100%" stopColor={g.color} stopOpacity={0.05} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} />
            <XAxis
              dataKey="name"
              interval="preserveStartEnd"
              minTickGap={12}
              tick={{ fontSize: 11, fill: tickFill }}
              stroke={axisStroke}
              tickLine={false}
            />
            <YAxis
              width={yAxisWidth}
              tickFormatter={(v) => valueFormatter(Number(v))}
              tick={{ fontSize: 12, fill: tickFill }}
              stroke={axisStroke}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              content={
                <ComparativeTooltip formatter={valueFormatter} classNames={cn} />
              }
            />
            {series.map((item, index) => (
              <Area
                key={item.dataKey}
                type={smooth ? "monotone" : "linear"}
                dataKey={item.dataKey}
                name={item.name}
                stroke={item.color}
                fill={`url(#${gradients[index]?.id})`}
                fillOpacity={1}
                strokeWidth={2}
                isAnimationActive={false}
              />
            ))}
          </AreaChart>
        </StableResponsiveContainer>
      </div>
    </div>
  );
}
