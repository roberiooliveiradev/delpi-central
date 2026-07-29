import { useId, useMemo, useState, type PointerEvent as ReactPointerEvent } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";
import { useDelpiDarkMode } from "../diagram/hooks/useDelpiDarkMode";
import {
  resolveSeriesChartStrokePoints,
  seriesChartPointsAttr,
} from "./seriesChartCurve";

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
  /** Gradiente suave (Catmull-Rom). Default true. */
  smooth?: boolean;
};

const DEFAULT_HEIGHT = 240;
const VIEW_W = 640;
const PAD_TOP = 12;
const PAD_RIGHT = 12;
const PAD_BOTTOM = 28;

export function comparativeAreaChartBemClasses(prefix: string) {
  const ui = "delpi-ui-comparative-area-chart";
  return {
    root: delpiUiClass(`${prefix}-comparative-area-chart`, ui),
    empty: delpiUiClass(`${prefix}-comparative-area-chart__empty`, `${ui}__empty`),
    canvas: delpiUiClass(`${prefix}-comparative-area-chart__canvas`, `${ui}__canvas`),
    svg: delpiUiClass(`${prefix}-comparative-area-chart__svg`, `${ui}__svg`),
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

function numericValue(point: ComparativeAreaChartPoint, dataKey: string): number {
  const raw = point[dataKey];
  const n = typeof raw === "number" ? raw : Number(raw);
  return Number.isFinite(n) ? n : 0;
}

function niceTicks(maxValue: number, count = 4): number[] {
  if (maxValue <= 0) return [0];
  const rough = maxValue / Math.max(1, count - 1);
  const pow = 10 ** Math.floor(Math.log10(rough));
  const niceStep = Math.ceil(rough / pow) * pow;
  const ticks: number[] = [];
  for (let v = 0; v <= maxValue + niceStep * 0.01; v += niceStep) {
    ticks.push(v);
    if (ticks.length > 8) break;
  }
  if (ticks[ticks.length - 1]! < maxValue) ticks.push(ticks[ticks.length - 1]! + niceStep);
  return ticks;
}

type HoverState = {
  index: number;
  clientX: number;
  clientY: number;
};

/**
 * Gráfico de área comparativo (SVG nativo) — padrão Transformômetro
 * (economia vs investimento / ganhos vs investimento).
 *
 * Sem Recharts: usa a mesma curva Catmull-Rom do series chart do kit.
 * Tema claro/escuro via `useDelpiDarkMode` + tokens `--delpi-ui-*`.
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
  const [hover, setHover] = useState<HoverState | null>(null);

  const layout = useMemo(() => {
    const padLeft = Math.max(48, yAxisWidth);
    const plotW = Math.max(40, VIEW_W - padLeft - PAD_RIGHT);
    const plotH = Math.max(40, height - PAD_TOP - PAD_BOTTOM);
    const maxValue = Math.max(
      0,
      ...data.flatMap((point) => series.map((s) => numericValue(point, s.dataKey))),
    );
    const yMax = maxValue > 0 ? maxValue * 1.08 : 1;
    const ticks = niceTicks(yMax);
    const axisMax = ticks[ticks.length - 1] ?? yMax;
    const n = Math.max(1, data.length);
    const toX = (index: number) => padLeft + (n <= 1 ? plotW / 2 : (index / (n - 1)) * plotW);
    const toY = (value: number) => PAD_TOP + plotH - (value / axisMax) * plotH;
    return { padLeft, plotW, plotH, axisMax, ticks, toX, toY, baseline: PAD_TOP + plotH };
  }, [data, series, height, yAxisWidth]);

  const areas = useMemo(
    () =>
      series.map((item) => {
        const anchors = data.map((point, index) => ({
          x: layout.toX(index),
          y: layout.toY(numericValue(point, item.dataKey)),
        }));
        const topCurve = resolveSeriesChartStrokePoints(anchors, smooth);
        const topPoints = seriesChartPointsAttr(topCurve);
        const first = topCurve[0];
        const last = topCurve[topCurve.length - 1];
        const areaPoints =
          first && last
            ? [`${first.x},${layout.baseline}`, topPoints, `${last.x},${layout.baseline}`].join(" ")
            : "";
        return {
          ...item,
          gradientDomId: `${gradientId}-${item.dataKey}`,
          topPoints,
          areaPoints,
          opacity: item.fillOpacity ?? 0.45,
        };
      }),
    [data, series, layout, smooth, gradientId],
  );

  if (!data.length) {
    return emptyMessage ? <p className={cn.empty}>{emptyMessage}</p> : null;
  }

  const tickFill = "var(--delpi-ui-muted, var(--text-muted, #64748b))";
  const gridStroke = isDark
    ? "color-mix(in srgb, var(--delpi-ui-border, #334155) 70%, transparent)"
    : "color-mix(in srgb, var(--delpi-ui-border, #e2e8f0) 85%, transparent)";
  const axisStroke = "var(--delpi-ui-border, var(--border, #e2e8f0))";

  const onMove = (event: ReactPointerEvent<SVGSVGElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const xRatio = (event.clientX - rect.left) / Math.max(1, rect.width);
    const xInView = xRatio * VIEW_W;
    let best = 0;
    let bestDist = Number.POSITIVE_INFINITY;
    for (let i = 0; i < data.length; i += 1) {
      const dist = Math.abs(layout.toX(i) - xInView);
      if (dist < bestDist) {
        bestDist = dist;
        best = i;
      }
    }
    setHover({ index: best, clientX: event.clientX, clientY: event.clientY });
  };

  const hoverPoint = hover ? data[hover.index] : null;

  return (
    <div className={rootClass} data-theme={isDark ? "dark" : "light"}>
      <div className={cn.canvas} style={{ height, position: "relative" }}>
        <svg
          className={cn.svg}
          viewBox={`0 0 ${VIEW_W} ${height}`}
          width="100%"
          height={height}
          role="img"
          aria-label="Gráfico de área comparativo"
          onPointerMove={onMove}
          onPointerLeave={() => setHover(null)}
        >
          <defs>
            {areas.map((area) => (
              <linearGradient
                key={area.gradientDomId}
                id={area.gradientDomId}
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop offset="0%" stopColor={area.color} stopOpacity={area.opacity} />
                <stop offset="100%" stopColor={area.color} stopOpacity={0.05} />
              </linearGradient>
            ))}
          </defs>

          {layout.ticks.map((tick) => {
            const y = layout.toY(tick);
            return (
              <g key={`tick-${tick}`}>
                <line
                  x1={layout.padLeft}
                  x2={VIEW_W - PAD_RIGHT}
                  y1={y}
                  y2={y}
                  stroke={gridStroke}
                  strokeDasharray="3 3"
                />
                <text
                  x={layout.padLeft - 8}
                  y={y + 4}
                  textAnchor="end"
                  fontSize={11}
                  fill={tickFill}
                >
                  {valueFormatter(tick)}
                </text>
              </g>
            );
          })}

          {data.map((point, index) => {
            const show =
              data.length <= 8 || index === 0 || index === data.length - 1 || index % Math.ceil(data.length / 6) === 0;
            if (!show) return null;
            return (
              <text
                key={`xlabel-${point.name}-${index}`}
                x={layout.toX(index)}
                y={height - 8}
                textAnchor="middle"
                fontSize={11}
                fill={tickFill}
              >
                {point.name}
              </text>
            );
          })}

          <line
            x1={layout.padLeft}
            x2={layout.padLeft}
            y1={PAD_TOP}
            y2={layout.baseline}
            stroke={axisStroke}
          />
          <line
            x1={layout.padLeft}
            x2={VIEW_W - PAD_RIGHT}
            y1={layout.baseline}
            y2={layout.baseline}
            stroke={axisStroke}
          />

          {areas.map((area) =>
            area.areaPoints ? (
              <g key={area.dataKey}>
                <polygon points={area.areaPoints} fill={`url(#${area.gradientDomId})`} stroke="none" />
                <polyline
                  points={area.topPoints}
                  fill="none"
                  stroke={area.color}
                  strokeWidth={2}
                  strokeLinejoin="round"
                  strokeLinecap="round"
                  vectorEffect="non-scaling-stroke"
                />
              </g>
            ) : null,
          )}

          {hover ? (
            <line
              x1={layout.toX(hover.index)}
              x2={layout.toX(hover.index)}
              y1={PAD_TOP}
              y2={layout.baseline}
              stroke={tickFill}
              strokeDasharray="4 4"
              pointerEvents="none"
            />
          ) : null}
        </svg>

        {hover && hoverPoint ? (
          <div
            className={cn.tooltip}
            role="status"
            style={{
              position: "fixed",
              left: hover.clientX + 12,
              top: hover.clientY + 12,
              zIndex: 20,
              pointerEvents: "none",
            }}
          >
            <p className={cn.tooltipLabel}>{String(hoverPoint.name ?? "")}</p>
            {series.map((item) => (
              <p key={item.dataKey} className={cn.tooltipRow} style={{ color: item.color }}>
                {item.name}: {valueFormatter(numericValue(hoverPoint, item.dataKey))}
              </p>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
