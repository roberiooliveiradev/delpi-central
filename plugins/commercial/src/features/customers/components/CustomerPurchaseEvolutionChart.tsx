import { useId, useMemo } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartCard, chartCardBemClasses, EmptyState } from "@delpi/plugin-ui/index";

import { CommercialSelectField, cmEmptyStateClassNames } from "../../../app/commercialUi";
import { CM_HELP } from "../../../content/helpTooltips";
import { formatCurrency } from "../../../utils/format";
import type {
  PurchaseEvolutionPoint,
  PurchaseEvolutionWindowMonths,
} from "../hooks/useCustomerPurchaseEvolution";

const CHART_CLASSES = chartCardBemClasses("cm", {
  headerLayout: "titleRow",
  wide: true,
});

const CHART_HEIGHT = 320;
const COLOR_CURRENT = "var(--cm-accent)";
const COLOR_PRIOR = "color-mix(in srgb, var(--cm-accent) 56%, var(--cm-text-muted))";

const PERIOD_OPTIONS: { value: string; label: string }[] = [
  { value: "6", label: "Últimos 6 meses" },
  { value: "12", label: "Últimos 12 meses" },
];

type CustomerPurchaseEvolutionChartProps = {
  points: PurchaseEvolutionPoint[];
  loading: boolean;
  error: string | null;
  windowMonths: PurchaseEvolutionWindowMonths;
  onWindowMonthsChange: (months: PurchaseEvolutionWindowMonths) => void;
};

function formatChartCurrency(value: number): string {
  if (!Number.isFinite(value)) return "—";
  const abs = Math.abs(value);
  if (abs >= 1_000_000) {
    return `R$ ${(value / 1_000_000).toLocaleString("pt-BR", {
      maximumFractionDigits: 1,
    })} mi`;
  }
  if (abs >= 1_000) {
    return `R$ ${(value / 1_000).toLocaleString("pt-BR", {
      maximumFractionDigits: 0,
    })} mil`;
  }
  return formatCurrency(value);
}

function parseWindowMonths(value: string): PurchaseEvolutionWindowMonths {
  return value === "6" ? 6 : 12;
}

export function CustomerPurchaseEvolutionChart({
  points,
  loading,
  error,
  windowMonths,
  onWindowMonthsChange,
}: CustomerPurchaseEvolutionChartProps) {
  const gradientId = useId().replace(/:/g, "");
  const hasValues = useMemo(
    () => points.some((p) => p.atual > 0 || p.anterior > 0),
    [points],
  );
  const totals = useMemo(
    () => ({
      atual: points.reduce((sum, point) => sum + (Number(point.atual) || 0), 0),
      anterior: points.reduce((sum, point) => sum + (Number(point.anterior) || 0), 0),
    }),
    [points],
  );

  const emptyMessage =
    windowMonths === 6
      ? "Sem faturamento registrado nos últimos 12 meses para este cliente."
      : "Sem faturamento registrado nos últimos 24 meses para este cliente.";

  return (
    <ChartCard
      title="Evolução de compras"
      titleHint={CM_HELP.customerDetail.purchaseEvolution}
      hint={CM_HELP.customerDetail.purchaseEvolutionComparison}
      classNames={CHART_CLASSES}
      className="cm-purchase-evolution"
      headerActions={
        <CommercialSelectField
          label="Período"
          hint={CM_HELP.customerDetail.purchaseEvolutionPeriod}
          options={PERIOD_OPTIONS}
          value={String(windowMonths)}
          onChange={(value) => onWindowMonthsChange(parseWindowMonths(value))}
          allowEmpty={false}
        />
      }
    >
      {error ? (
        <EmptyState
          classNames={cmEmptyStateClassNames}
          defaultMessage={error}
          role="alert"
        />
      ) : loading && !hasValues ? (
        <EmptyState
          classNames={cmEmptyStateClassNames}
          defaultMessage="Carregando evolução…"
        />
      ) : !hasValues ? (
        <EmptyState
          classNames={cmEmptyStateClassNames}
          defaultMessage={emptyMessage}
        />
      ) : (
        <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
          <ComposedChart
            data={points}
            margin={{ top: 8, right: 16, left: 4, bottom: 4 }}
          >
            <defs>
              <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={COLOR_CURRENT} stopOpacity={0.22} />
                <stop offset="100%" stopColor={COLOR_CURRENT} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="periodo"
              tick={{ fontSize: 11 }}
              interval="preserveStartEnd"
              tickLine={false}
            />
            <YAxis
              width={88}
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => formatChartCurrency(Number(value))}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              formatter={(value, name) => [
                formatCurrency(typeof value === "number" ? value : Number(value)),
                name === "atual" ? "Período atual" : "Período anterior",
              ]}
            />
            <Legend
              verticalAlign="top"
              align="left"
              wrapperStyle={{ paddingBottom: 8, fontSize: 13 }}
              formatter={(value) => {
                if (value === "atual") {
                  return `Período atual · ${formatCurrency(totals.atual)}`;
                }
                return `Período anterior · ${formatCurrency(totals.anterior)}`;
              }}
            />
            <Area
              type="monotone"
              dataKey="atual"
              name="atual"
              stroke={COLOR_CURRENT}
              strokeWidth={2.25}
              fill={`url(#${gradientId})`}
              dot={{ r: 3.5, fill: COLOR_CURRENT, strokeWidth: 0 }}
              activeDot={{ r: 6, strokeWidth: 0 }}
            />
            <Line
              type="monotone"
              dataKey="anterior"
              name="anterior"
              stroke={COLOR_PRIOR}
              strokeWidth={2}
              strokeOpacity={0.9}
              dot={{ r: 3.5, fill: COLOR_PRIOR, strokeWidth: 0 }}
              activeDot={{ r: 6, strokeWidth: 0 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      )}
    </ChartCard>
  );
}
