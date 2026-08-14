import { useId, useMemo } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { EmptyState } from "@delpi/plugin-ui/index";

import {
  CommercialActionButton,
  CommercialChartToolbar,
  CommercialSectionCard,
  CommercialStateBanner,
  cmEmptyStateClassNames,
  useChartGranularitySelection,
} from "../../../../app/commercialUi";
import { CUSTOMER_BILLING_CONTENT } from "../../../../content/customerBillingContent";
import { CM_HELP } from "../../../../content/helpTooltips";
import { formatCurrency } from "../../../../utils/format";
import { useCustomerBillingSeries } from "../../hooks/useCustomerBillingSeries";
import type { CustomerSummary } from "../../types/customerSummary";
import {
  BILLING_SERIES_GRANULARITY_OPTIONS,
  allowedBillingSeriesGranularities,
} from "../../utils/billingSeriesPeriod";

const CHART_HEIGHT = 280;
const SERIES_COLOR = "var(--cm-accent)";
const PRIOR_SERIES_COLOR = "var(--chart-3, #94a3b8)";

type CustomerAccountBillingChartProps = {
  codigo: string;
  loja: string;
  startDate: string;
  endDate: string;
  comparePriorYear: boolean;
  /** Desliga fetch (aba oculta / validação de período). */
  enabled?: boolean;
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

/** Stub mínimo para o hook de série (só código+loja entram no request). */
function accountAsSeriesCustomer(codigo: string, loja: string): CustomerSummary {
  const code = codigo.trim();
  const store = loja.trim();
  return {
    key: `${code}|${store}`,
    codigo: code,
    loja: store,
    nome: code,
    quantidadePedidosAbertos: 0,
    quantidadeLinhasAbertas: 0,
    valorTotalAberto: 0,
    quantidadePedidosAtrasados: 0,
    maiorAtrasoDias: 0,
    proximaEntrega: null,
    quantidadePedidosParciais: 0,
    temAtraso: false,
    temPedidoParcial: false,
    lines: [],
  };
}

/**
 * Série de faturamento da Conta (Histórico) — período e YoY vêm dos filtros da aba.
 */
export function CustomerAccountBillingChart({
  codigo,
  loja,
  startDate,
  endDate,
  comparePriorYear,
  enabled = true,
}: CustomerAccountBillingChartProps) {
  const gradientId = useId().replace(/:/g, "");
  const customers = useMemo(
    () => [accountAsSeriesCustomer(codigo, loja)],
    [codigo, loja],
  );
  const queryEnabled =
    enabled && Boolean(codigo.trim() && loja.trim() && startDate && endDate);
  const allowedGrains = allowedBillingSeriesGranularities(startDate, endDate);
  const { granularity, setGranularity } = useChartGranularitySelection(
    startDate,
    endDate,
  );
  const effectiveGrain = allowedGrains.includes(granularity)
    ? granularity
    : (allowedGrains[0] ?? "month");

  const { points, loading, error, totalValue, coverage, reload } =
    useCustomerBillingSeries(customers, {
      enabled: queryEnabled,
      startDate,
      endDate,
      granularity: effectiveGrain,
      comparePriorYear,
    });

  const chartData = useMemo(
    () =>
      points.map((point) => ({
        periodo: point.label,
        faturamento: Number(point.value) || 0,
        faturamento_prior:
          point.value_prior == null ? null : Number(point.value_prior) || 0,
      })),
    [points],
  );

  const hasValues = chartData.some(
    (point) =>
      point.faturamento > 0 ||
      (comparePriorYear &&
        point.faturamento_prior != null &&
        point.faturamento_prior > 0),
  );

  return (
    <div className="cm-billing-series-chart cm-account-billing-chart">
      <CommercialSectionCard
        title="Faturamento no período"
        hint={CM_HELP.customerDetail.billingSeriesAccount}
        subtitle={
          loading
            ? "Atualizando série…"
            : hasValues
              ? `Total no período: ${formatCurrency(totalValue)}`
              : undefined
        }
        actions={
          queryEnabled ? (
            <CommercialChartToolbar
              granularity={effectiveGrain}
              onGranularityChange={setGranularity}
              options={BILLING_SERIES_GRANULARITY_OPTIONS}
              modes={allowedGrains}
              granularityHelp={CM_HELP.customers.billingSeriesGrain}
            />
          ) : null
        }
      >
        {error && !hasValues ? (
          <EmptyState
            classNames={cmEmptyStateClassNames}
            defaultMessage={error}
            role="alert"
          />
        ) : loading && !hasValues ? (
          <EmptyState
            classNames={cmEmptyStateClassNames}
            defaultMessage="Carregando faturamento…"
          />
        ) : !hasValues ? (
          <EmptyState
            classNames={cmEmptyStateClassNames}
            defaultMessage="Sem faturamento registrado neste período para o cliente."
          />
        ) : (
          <>
            {error ? (
              <CommercialStateBanner>
                <p>
                  {error} Cobertura: {coverage.covered}/{coverage.total}.
                </p>
                <CommercialActionButton
                  variant="ghost"
                  onClick={reload}
                  disabled={loading}
                >
                  Tentar novamente
                </CommercialActionButton>
              </CommercialStateBanner>
            ) : null}
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
                  formatter={(value, name) => [
                    value == null || Number.isNaN(Number(value))
                      ? "—"
                      : formatCurrency(Number(value)),
                    name,
                  ]}
                  labelFormatter={(label) => String(label)}
                />
                {comparePriorYear ? <Legend /> : null}
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
                {comparePriorYear ? (
                  <Line
                    type="monotone"
                    dataKey="faturamento_prior"
                    name="Ano ant."
                    stroke={PRIOR_SERIES_COLOR}
                    strokeWidth={2}
                    strokeDasharray="6 4"
                    connectNulls
                    dot={false}
                  />
                ) : null}
              </AreaChart>
            </ResponsiveContainer>
          </>
        )}
        <p className="cm-customer-billing-filters__hint cm-cell-muted">
          {CUSTOMER_BILLING_CONTENT.cancelledInvoicesHint}
        </p>
      </CommercialSectionCard>
    </div>
  );
}
