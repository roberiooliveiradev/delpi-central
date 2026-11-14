import { useId, useMemo, useRef, useState, type KeyboardEvent } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";
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
  /**
   * Click / Enter on an X-axis point. Also makes the points keyboard
   * navigable (ArrowLeft/ArrowRight/Home/End, Enter or Space selects).
   */
  onPointSelect?: (point: ComparativeAreaChartPoint, index: number) => void;
  /** `name` of the selected point: draws a vertical highlight band on it. */
  selectedName?: string | null;
  /** Accessible name of a point target. Default lists each series value. */
  pointAriaLabel?: (point: ComparativeAreaChartPoint) => string;
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
    points: delpiUiClass(`${prefix}-comparative-area-chart__points`, `${ui}__points`),
    point: delpiUiClass(`${prefix}-comparative-area-chart__point`, `${ui}__point`),
    selectionBand: delpiUiClass(
      `${prefix}-comparative-area-chart__selection-band`,
      `${ui}__selection-band`,
    ),
    focusBand: delpiUiClass(
      `${prefix}-comparative-area-chart__focus-band`,
      `${ui}__focus-band`,
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
  onPointSelect,
  selectedName,
  pointAriaLabel,
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

  const pointRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const [focusedIndex, setFocusedIndex] = useState<number | null>(null);

  if (!data.length) {
    return emptyMessage ? <p className={cn.empty}>{emptyMessage}</p> : null;
  }

  const interactive = typeof onPointSelect === "function";
  const selectedIndex =
    selectedName != null ? data.findIndex((point) => point.name === selectedName) : -1;
  const focusName =
    focusedIndex != null && focusedIndex !== selectedIndex ? data[focusedIndex]?.name : undefined;
  const rovingIndex = focusedIndex ?? (selectedIndex >= 0 ? selectedIndex : 0);

  const describePoint = (point: ComparativeAreaChartPoint): string => {
    if (pointAriaLabel) return pointAriaLabel(point);
    const values = series
      .map((item) => {
        const raw = point[item.dataKey];
        return typeof raw === "number" ? `${item.name}: ${valueFormatter(raw)}` : null;
      })
      .filter(Boolean)
      .join("; ");
    return values ? `${point.name}: ${values}` : String(point.name);
  };

  const moveFocus = (next: number) => {
    const bounded = Math.min(data.length - 1, Math.max(0, next));
    pointRefs.current[bounded]?.focus();
  };

  const handlePointKeyDown = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    switch (event.key) {
      case "ArrowRight":
      case "ArrowDown":
        event.preventDefault();
        moveFocus(index + 1);
        break;
      case "ArrowLeft":
      case "ArrowUp":
        event.preventDefault();
        moveFocus(index - 1);
        break;
      case "Home":
        event.preventDefault();
        moveFocus(0);
        break;
      case "End":
        event.preventDefault();
        moveFocus(data.length - 1);
        break;
      case "Enter":
        // Handled here (and prevented) so the native Enter→click does not fire twice.
        event.preventDefault();
        onPointSelect?.(data[index]!, index);
        break;
      default:
        break;
    }
  };

  const canvasClass = interactive ? withBemModifier(cn.canvas, "interactive") : cn.canvas;

  return (
    <div className={rootClass} data-theme={isDark ? "dark" : "light"}>
      <div className={canvasClass} style={{ height }}>
        <StableResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
            onClick={
              interactive
                ? (state) => {
                    const raw = state?.activeTooltipIndex;
                    const index = raw == null ? -1 : Number(raw);
                    const point = Number.isInteger(index) ? data[index] : undefined;
                    if (point) onPointSelect?.(point, index);
                  }
                : undefined
            }
          >
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
            {focusName != null ? (
              <ReferenceLine x={focusName} className={cn.focusBand} stroke="currentColor" />
            ) : null}
            {selectedIndex >= 0 ? (
              <ReferenceLine x={selectedName!} className={cn.selectionBand} stroke="currentColor" />
            ) : null}
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
      {interactive ? (
        <div className={cn.points} role="group">
          {data.map((point, index) => (
            <button
              key={`${point.name}-${index}`}
              ref={(node) => {
                pointRefs.current[index] = node;
              }}
              type="button"
              className={cn.point}
              tabIndex={index === rovingIndex ? 0 : -1}
              aria-pressed={selectedName != null ? index === selectedIndex : undefined}
              aria-label={describePoint(point)}
              onFocus={() => setFocusedIndex(index)}
              onBlur={() => setFocusedIndex((current) => (current === index ? null : current))}
              onKeyDown={(event) => handlePointKeyDown(event, index)}
              onClick={() => onPointSelect?.(point, index)}
            >
              {String(point.name)}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
