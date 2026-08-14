import { useMemo } from "react";
import {
  ChartTypeSegmentToggle,
  ChartViewShell,
  EmptyState,
  MultiTypeSeriesChart,
  NativeCheckboxControl,
  TIME_MULTI_SERIES_TYPES,
  runTabularExport,
  usePersistedChartPreferences,
  type MultiTypeSeriesSpec,
} from "@delpi/plugin-ui/index";

import {
  CommercialActionButton,
  CommercialChartToolbar,
  CommercialSectionCard,
  CommercialStateBanner,
  CommercialTabularExportButtons,
  cmEmptyStateClassNames,
  useChartGranularitySelection,
} from "../../../../app/commercialUi";
import { CUSTOMER_BILLING_CONTENT } from "../../../../content/customerBillingContent";
import { CM_HELP } from "../../../../content/helpTooltips";
import { formatCurrency } from "../../../../utils/format";
import { buildBillingSeriesExportPayload } from "../../utils/billingSeriesExportBuilders";
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
  const { preferences, setPreferences, setChartType } = usePersistedChartPreferences({
    storageKey: "commercial:account:billing-series",
    defaults: { chartType: "column", showTrend: false },
    allowedChartTypes: TIME_MULTI_SERIES_TYPES,
  });
  const showTrend = Boolean(preferences.showTrend);
  const chartType = preferences.chartType ?? "column";
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

  const bars = useMemo((): MultiTypeSeriesSpec[] => {
    const list: MultiTypeSeriesSpec[] = [
      {
        dataKey: "faturamento",
        name: "Faturamento",
        fill: SERIES_COLOR,
        trendSource: true,
      },
    ];
    if (comparePriorYear) {
      list.push({
        dataKey: "faturamento_prior",
        name: "Ano ant.",
        fill: PRIOR_SERIES_COLOR,
      });
    }
    return list;
  }, [comparePriorYear]);

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
            <ChartViewShell
              prefix="cm"
              typeToggle={
                <ChartTypeSegmentToggle
                  family="time_multi_series"
                  value={chartType}
                  onChange={setChartType}
                  idPrefix="account-billing-type"
                  prefix="cm"
                />
              }
              exportActions={
                <CommercialTabularExportButtons
                  compact
                  disabled={!hasValues || loading}
                  onExport={(format) => {
                    runTabularExport({
                      kind: "table",
                      format,
                      payload: buildBillingSeriesExportPayload(chartData, {
                        title: "Faturamento no período",
                        compareYears: comparePriorYear ? 1 : 0,
                      }),
                    });
                  }}
                />
              }
              overlays={
                <NativeCheckboxControl
                  id="customer-account-billing-trend"
                  checked={showTrend}
                  onChange={(checked) => setPreferences({ showTrend: checked })}
                  label={CUSTOMER_BILLING_CONTENT.showTrendLine}
                  hint={CM_HELP.customerDetail.billingSeriesTrend}
                  hintPlacement="tooltip"
                  hintAriaLabel="Ajuda: linha de tendência"
                />
              }
            >
              <MultiTypeSeriesChart
                data={chartData}
                categoryKey="periodo"
                series={bars}
                chartType={chartType}
                height={CHART_HEIGHT}
                showTrend={showTrend}
                showLegend={comparePriorYear || showTrend}
                trendSeriesName={CUSTOMER_BILLING_CONTENT.trendLineSeriesName}
                formatY={formatChartCurrency}
                formatTooltipValue={formatCurrency}
              />
            </ChartViewShell>
          </>
        )}
        <p className="cm-customer-billing-filters__hint cm-cell-muted">
          {CUSTOMER_BILLING_CONTENT.cancelledInvoicesHint}
        </p>
      </CommercialSectionCard>
    </div>
  );
}
