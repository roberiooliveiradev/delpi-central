import { useMemo, useState } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type {
  SafetyStockProjectionLedgerEntry,
  SafetyStockProjectionSummary,
} from "../types/safetyStock";
import {
  buildBalanceTimelineSeries,
  type BalanceTimelinePoint,
} from "../utils/buildBalanceTimelineSeries";
import { formatIsoDatePtBr } from "../utils/safetyStockStatus";

const CHART_HEIGHT = 340;

type ProjectionViewMode = "with_orders" | "without_orders";

type StockProjectionChartProps = {
  items: SafetyStockProjectionLedgerEntry[];
  summary: SafetyStockProjectionSummary;
  periodConsumption?: number;
  periodStart?: string | null;
  periodEnd?: string | null;
};

function formatCompactAxis(value: number): string {
  const abs = Math.abs(value);
  const sign = value < 0 ? "-" : "";
  if (abs >= 1_000_000) {
    const scaled = abs / 1_000_000;
    const text = scaled.toLocaleString("pt-BR", {
      maximumFractionDigits: scaled >= 10 ? 0 : 1,
    });
    return `${sign}${text} mi`;
  }
  if (abs >= 1_000) {
    const scaled = abs / 1_000;
    const text = scaled.toLocaleString("pt-BR", {
      maximumFractionDigits: scaled >= 100 ? 0 : 0,
    });
    return `${sign}${text} mil`;
  }
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 0 });
}

function formatTooltipValue(value: number): string {
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: Math.abs(value) >= 100 ? 0 : 2,
    maximumFractionDigits: Math.abs(value) >= 100 ? 0 : 2,
  });
}

function monthTicksFromPoints(points: BalanceTimelinePoint[]): string[] {
  return points.filter((point) => point.monthTick).map((point) => point.date);
}

export function StockProjectionChart({
  items,
  summary,
  periodConsumption = 0,
  periodStart = null,
  periodEnd = null,
}: StockProjectionChartProps) {
  const [viewMode, setViewMode] = useState<ProjectionViewMode>("with_orders");
  const includePurchaseOrders = viewMode === "with_orders";

  const series = useMemo(
    () =>
      buildBalanceTimelineSeries(items, summary, {
        periodConsumption,
        periodStart,
        periodEnd,
        includePurchaseOrders,
      }),
    [items, summary, periodConsumption, periodStart, periodEnd, includePurchaseOrders],
  );

  const chartData = useMemo(() => {
    if (!series) return [];
    return series.points.map((point) => ({
      ...point,
      linePositive: point.balance >= 0 ? point.balance : null,
      lineNegative: point.balance < 0 ? point.balance : null,
    }));
  }, [series]);

  if (!series || series.points.length === 0) {
    return <p className="ess-detail__empty">Sem pontos para a linha do tempo do saldo.</p>;
  }

  const monthTicks = monthTicksFromPoints(series.points);
  const shortageDate = series.firstShortageDate;
  const periodLabel = `Período: ${formatIsoDatePtBr(series.periodStart)} até ${formatIsoDatePtBr(series.periodEnd)}`;
  const subtitle = includePurchaseOrders
    ? "Projeção diária dos próximos 12 meses considerando consumo em dias úteis e entradas de pedidos futuros."
    : "Projeção diária dos próximos 12 meses considerando apenas consumo em dias úteis, sem entradas de pedidos de compra.";

  return (
    <div className="ess-projection-timeline">
      <div className="ess-projection-timeline__header">
        <div className="ess-projection-timeline__titles">
          <h4 className="ess-projection-timeline__title">Linha do tempo do saldo</h4>
          <p className="ess-projection-timeline__subtitle">{subtitle}</p>
        </div>
        <div className="ess-projection-timeline__controls">
          <div
            className="ess-chart-tabs ess-projection-timeline__view-tabs"
            role="tablist"
            aria-label="Visão da projeção com ou sem pedidos de compra"
          >
            <button
              type="button"
              role="tab"
              aria-selected={includePurchaseOrders}
              className={
                includePurchaseOrders
                  ? "ess-chart-tabs__btn ess-chart-tabs__btn--active"
                  : "ess-chart-tabs__btn"
              }
              onClick={() => setViewMode("with_orders")}
            >
              Com pedidos
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={!includePurchaseOrders}
              className={
                !includePurchaseOrders
                  ? "ess-chart-tabs__btn ess-chart-tabs__btn--active"
                  : "ess-chart-tabs__btn"
              }
              onClick={() => setViewMode("without_orders")}
            >
              Sem pedidos
            </button>
          </div>
          <span className="ess-projection-timeline__period">{periodLabel}</span>
        </div>
      </div>

      <div className="ess-modern-line-chart ess-projection-chart">
        <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
          <ComposedChart
            data={chartData}
            margin={{ top: 36, right: 24, bottom: 8, left: 8 }}
            accessibilityLayer
          >
            <defs>
              <linearGradient id="essBalancePositiveFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#16a34a" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#16a34a" stopOpacity={0.05} />
              </linearGradient>
              <linearGradient id="essBalanceNegativeFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#dc2626" stopOpacity={0.08} />
                <stop offset="100%" stopColor="#dc2626" stopOpacity={0.32} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="var(--ess-border)" strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              ticks={monthTicks}
              tickFormatter={(value: string) => {
                const point = series.points.find((item) => item.date === value);
                return point?.monthTick ?? "";
              }}
              tick={{ fontSize: 11, fill: "var(--ess-text-muted)" }}
              axisLine={{ stroke: "var(--ess-border)" }}
              tickLine={false}
              minTickGap={24}
            />
            <YAxis
              tick={{ fontSize: 12, fill: "var(--ess-text-muted)" }}
              tickFormatter={(value: number) => formatCompactAxis(value)}
              axisLine={false}
              tickLine={false}
              width={72}
            />
            <Tooltip
              labelFormatter={(label) => formatIsoDatePtBr(String(label))}
              formatter={(value, name) => {
                if (name !== "Saldo") return [null as unknown as string, ""];
                return [
                  formatTooltipValue(typeof value === "number" ? value : Number(value)),
                  "Saldo",
                ];
              }}
              contentStyle={{
                background: "var(--ess-surface)",
                border: "1px solid var(--ess-border)",
                borderRadius: 12,
                color: "var(--ess-text)",
              }}
              labelStyle={{ color: "var(--ess-title)", fontWeight: 700 }}
            />
            <ReferenceLine y={0} stroke="var(--ess-border-strong, #94a3b8)" strokeWidth={1.5} />
            <Area
              type="monotone"
              dataKey="balancePositive"
              stroke="none"
              fill="url(#essBalancePositiveFill)"
              isAnimationActive={false}
              legendType="none"
            />
            <Area
              type="monotone"
              dataKey="balanceNegative"
              stroke="none"
              fill="url(#essBalanceNegativeFill)"
              isAnimationActive={false}
              legendType="none"
            />
            <Line
              type="monotone"
              dataKey="linePositive"
              name="Saldo"
              stroke="#16a34a"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
              connectNulls={false}
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="lineNegative"
              name="Saldo"
              stroke="#dc2626"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
              connectNulls={false}
              isAnimationActive={false}
              legendType="none"
            />
            {shortageDate ? (
              <ReferenceLine
                x={shortageDate}
                stroke="#dc2626"
                strokeDasharray="4 4"
                strokeWidth={1.5}
                label={{
                  value: `Ruptura: ${formatIsoDatePtBr(shortageDate)}`,
                  position: "insideTopLeft",
                  fill: "#b91c1c",
                  fontSize: 12,
                  fontWeight: 600,
                }}
              />
            ) : null}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
