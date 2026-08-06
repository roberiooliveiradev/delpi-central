import { useId, useMemo } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartCard, chartCardBemClasses } from "@delpi/plugin-ui/index";

import { CM_HELP } from "../../../content/helpTooltips";
import { formatCurrency } from "../../../utils/format";
import {
  BILLING_SERIES_ALL_KEY,
  useCustomerBillingSeries,
} from "../hooks/useCustomerBillingSeries";
import type { CustomerSummary } from "../types/customerSummary";

const CHART_CLASSES = chartCardBemClasses("pva", {
  headerLayout: "titleRow",
  wide: true,
});

/** Mesma altura do gráfico ROL do dashboard comercial. */
const CHART_HEIGHT = 320;

/** Accent DELPI — alinhado ao comercial (série primária). */
const SERIES_COLOR = "#089bdb";

type CustomerBillingSeriesChartProps = {
  customers: CustomerSummary[];
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

/**
 * Faturamento mensal (12 meses) — Recharts (mesmo padrão do dashboard comercial).
 */
export function CustomerBillingSeriesChart({ customers }: CustomerBillingSeriesChartProps) {
  const gradientId = useId().replace(/:/g, "");
  const {
    selectedKey,
    setSelectedKey,
    customerOptions,
    points,
    loading,
    error,
    totalValue,
  } = useCustomerBillingSeries(customers);

  const chartData = useMemo(
    () =>
      points.map((point) => ({
        periodo: point.label,
        faturamento: Number(point.value) || 0,
      })),
    [points],
  );

  const hasValues = chartData.some((point) => point.faturamento > 0);
  const filterLabel =
    selectedKey === BILLING_SERIES_ALL_KEY
      ? "Toda a carteira"
      : customerOptions.find((c) => c.key === selectedKey)?.nome ?? "Cliente";

  return (
    <ChartCard
      title="Faturamento — últimos 12 meses"
      titleHint={CM_HELP.customers.billingSeries}
      hint={
        loading
          ? "Atualizando série…"
          : hasValues
            ? `Total no período · ${filterLabel}: ${formatCurrency(totalValue)}`
            : undefined
      }
      classNames={CHART_CLASSES}
      className="pva-billing-series-chart"
      headerActions={
        <label className="pva-billing-series-chart__filter">
          <span className="visually-hidden">Filtrar por cliente</span>
          <select
            className="pva-customers-toolbar__select pva-billing-series-chart__select"
            value={selectedKey}
            onChange={(event) => setSelectedKey(event.target.value)}
            disabled={loading && customerOptions.length === 0}
          >
            <option value={BILLING_SERIES_ALL_KEY}>Todos os clientes</option>
            {customerOptions.map((customer) => (
              <option key={customer.key} value={customer.key}>
                {customer.nome} ({customer.codigo}/{customer.loja})
              </option>
            ))}
          </select>
        </label>
      }
    >
      {error ? (
        <p className="pva-billing-series-chart__empty" role="alert">
          {error}
        </p>
      ) : loading && !hasValues ? (
        <p className="pva-billing-series-chart__empty" aria-busy="true">
          Carregando faturamento…
        </p>
      ) : !hasValues ? (
        <p className="pva-billing-series-chart__empty">
          Sem faturamento registrado nos últimos 12 meses
          {selectedKey === BILLING_SERIES_ALL_KEY ? " para a carteira" : " para este cliente"}.
        </p>
      ) : (
        <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
          <AreaChart
            data={chartData}
            margin={{ top: 12, right: 16, left: 4, bottom: 4 }}
          >
            <defs>
              <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={SERIES_COLOR} stopOpacity={0.35} />
                <stop offset="100%" stopColor={SERIES_COLOR} stopOpacity={0.02} />
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
              formatter={(value) => [
                formatCurrency(typeof value === "number" ? value : Number(value)),
                "Faturamento",
              ]}
              labelFormatter={(label) => String(label)}
            />
            <Area
              type="monotone"
              dataKey="faturamento"
              name="Faturamento"
              stroke={SERIES_COLOR}
              strokeWidth={2}
              fill={`url(#${gradientId})`}
              dot={{ r: 3, fill: SERIES_COLOR, strokeWidth: 0 }}
              activeDot={{ r: 5 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </ChartCard>
  );
}
