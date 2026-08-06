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
import type { PurchaseEvolutionPoint } from "../hooks/useCustomerPurchaseEvolution";

const CHART_CLASSES = chartCardBemClasses("pva", {
  headerLayout: "titleRow",
  wide: true,
});

const CHART_HEIGHT = 320;
const COLOR_CURRENT = "#003866";
const COLOR_PRIOR = "#089bdb";

type CustomerPurchaseEvolutionChartProps = {
  points: PurchaseEvolutionPoint[];
  loading: boolean;
  error: string | null;
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

export function CustomerPurchaseEvolutionChart({
  points,
  loading,
  error,
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

  return (
    <ChartCard
      title="Evolução de compras"
      titleHint={CM_HELP.customerDetail.purchaseEvolution}
      hint="Comparativo: últimos 12 meses × 12 meses anteriores"
      classNames={CHART_CLASSES}
      className="pva-purchase-evolution"
      headerActions={
        <CommercialSelectField
          label="Período"
          options={[{ value: "12", label: "Últimos 12 meses" }]}
          value="12"
          onChange={() => undefined}
          allowEmpty={false}
          disabled
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
          defaultMessage="Sem faturamento registrado nos últimos 24 meses para este cliente."
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
