import { useMemo } from "react";
import {
  ChartOverlayOptionsPopover,
  ChartTypeSegmentToggle,
  ChartViewShell,
  EmptyState,
  MultiTypeSeriesChart,
  TIME_MULTI_SERIES_TYPES,
  runTabularExport,
  usePersistedChartPreferences,
  type ChartOverlayOption,
  type MultiTypeSeriesSpec,
} from "@delpi/plugin-ui/index";

import {
  CommercialActionButton,
  CommercialChartGranularityToggle,
  CommercialSectionCard,
  CommercialStateBanner,
  CommercialTabularExportButtons,
  cmEmptyStateClassNames,
  useChartGranularitySelection,
} from "../../../../app/commercialUi";
import { ANALYTICS_CONTENT } from "../../../../content/analyticsContent";
import {
  billingMetricShortLabel,
  formatChartMetricValue,
  formatMetricTotal,
  type PortfolioBillingMetric,
} from "../../../../content/billingMetric";
import { CUSTOMER_BILLING_CONTENT } from "../../../../content/customerBillingContent";
import { CM_HELP } from "../../../../content/helpTooltips";
import { formatCurrency, formatQuantity } from "../../../../utils/format";
import { resolveCalendarBucketFraction } from "../../../../utils/linearTrendSeries";
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
  onComparePriorYearChange: (value: boolean) => void;
  billingMetric?: PortfolioBillingMetric;
  /** Desliga fetch (aba oculta / validação de período). */
  enabled?: boolean;
};

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
 * Série de faturamento/quantidade da Conta (Histórico) — período nos filtros; YoY nas Opções do gráfico.
 */
export function CustomerAccountBillingChart({
  codigo,
  loja,
  startDate,
  endDate,
  comparePriorYear,
  onComparePriorYearChange,
  billingMetric = "value",
  enabled = true,
}: CustomerAccountBillingChartProps) {
  const { preferences, setPreferences, setChartType } = usePersistedChartPreferences({
    storageKey: "commercial:account:billing-series",
    defaults: {
      chartType: "column",
      showTrend: false,
      incompleteBucketMode: "exclude",
    },
    allowedChartTypes: TIME_MULTI_SERIES_TYPES,
  });
  const showTrend = Boolean(preferences.showTrend);
  const incompleteBucketMode =
    preferences.incompleteBucketMode === "weightByFraction"
      ? "weightByFraction"
      : "exclude";
  const chartType = preferences.chartType ?? "column";

  const overlayOptions = useMemo((): ChartOverlayOption[] => {
    return [
      {
        id: "yoy",
        label: ANALYTICS_CONTENT.overview.comparePriorYear,
        checked: comparePriorYear,
        onChange: onComparePriorYearChange,
        hint: CM_HELP.customerDetail.billingSeriesAccount,
        hintAriaLabel: "Ajuda: comparar ano anterior",
      },
      {
        id: "trend",
        label: CUSTOMER_BILLING_CONTENT.showTrendLine,
        checked: showTrend,
        onChange: (checked) => setPreferences({ showTrend: checked }),
        hint: CM_HELP.customerDetail.billingSeriesTrend,
        hintAriaLabel: "Ajuda: linha de tendência",
      },
      {
        id: "trend-weight",
        label: "Ponderar período parcial",
        checked: incompleteBucketMode === "weightByFraction",
        onChange: (checked) =>
          setPreferences({
            incompleteBucketMode: checked ? "weightByFraction" : "exclude",
          }),
        hint: CM_HELP.customers.billingTrendIncomplete,
        hintAriaLabel: "Ajuda: tendência em período parcial",
        disabled: !showTrend,
      },
    ];
  }, [
    comparePriorYear,
    incompleteBucketMode,
    onComparePriorYearChange,
    setPreferences,
    showTrend,
  ]);

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
      metric: billingMetric,
    });

  const chartData = useMemo(
    () =>
      points.map((point) => ({
        periodo: point.label,
        faturamento: Number(point.value) || 0,
        faturamento_prior:
          point.value_prior == null ? null : Number(point.value_prior) || 0,
        _bucketFraction: resolveCalendarBucketFraction(
          point.date_start,
          point.date_end,
        ),
      })),
    [points],
  );

  const seriesName =
    billingMetric === "quantity" ? "Quantidade fornecida" : "Faturamento";
  const bars = useMemo((): MultiTypeSeriesSpec[] => {
    const list: MultiTypeSeriesSpec[] = [
      {
        dataKey: "faturamento",
        name: seriesName,
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
  }, [comparePriorYear, seriesName]);

  const hasValues = chartData.some(
    (point) =>
      point.faturamento > 0 ||
      (comparePriorYear &&
        point.faturamento_prior != null &&
        point.faturamento_prior > 0),
  );

  const chartTitle =
    billingMetric === "quantity"
      ? "Quantidade fornecida no período"
      : "Faturamento no período";
  const metricLabel = billingMetricShortLabel(billingMetric);
  const totalLabel = formatMetricTotal(totalValue, billingMetric);
  const formatAxis = (value: number) => formatChartMetricValue(value, billingMetric);
  const formatTip =
    billingMetric === "quantity" ? formatQuantity : formatCurrency;
  const emptyMessage =
    billingMetric === "quantity"
      ? "Sem quantidade fornecida registrada neste período para o cliente."
      : "Sem faturamento registrado neste período para o cliente.";

  return (
    <div className="cm-billing-series-chart cm-account-billing-chart">
      <CommercialSectionCard
        title={chartTitle}
        hint={CM_HELP.customerDetail.billingSeriesAccount}
        subtitle={
          loading
            ? "Atualizando série…"
            : hasValues
              ? `Total no período · ${metricLabel}: ${totalLabel}`
              : undefined
        }
        actions={undefined}
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
            defaultMessage="Carregando série…"
          />
        ) : !hasValues ? (
          <EmptyState
            classNames={cmEmptyStateClassNames}
            defaultMessage={emptyMessage}
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
              granularityLabel={ANALYTICS_CONTENT.overview.chartGranularityLabel}
              overlaysLabel={ANALYTICS_CONTENT.overview.chartOverlaysLabel}
              typeToggleLabel={ANALYTICS_CONTENT.overview.chartTypeLabel}
              granularity={
                queryEnabled ? (
                  <CommercialChartGranularityToggle
                    value={effectiveGrain}
                    onChange={setGranularity}
                    options={BILLING_SERIES_GRANULARITY_OPTIONS}
                    modes={allowedGrains}
                    idPrefix="account-billing"
                  />
                ) : null
              }
              overlays={
                <ChartOverlayOptionsPopover
                  idPrefix="account-billing-overlays"
                  portalScopeClassName="dashboard-commercial"
                  panelTitle={ANALYTICS_CONTENT.overview.chartOverlaysPanelTitle}
                  emptySummaryLabel={ANALYTICS_CONTENT.overview.chartOverlaysEmpty}
                  options={overlayOptions}
                />
              }
              typeToggle={
                <ChartTypeSegmentToggle
                  family="time_multi_series"
                  value={chartType}
                  onChange={setChartType}
                  idPrefix="account-billing-type"
                  prefix="cm"
                  portalScopeClassName="dashboard-commercial"
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
                        title: chartTitle,
                        compareYears: comparePriorYear ? 1 : 0,
                      }),
                    });
                  }}
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
                incompleteBucketMode={incompleteBucketMode}
                showLegend={comparePriorYear || showTrend}
                trendSeriesName={CUSTOMER_BILLING_CONTENT.trendLineSeriesName}
                formatY={formatAxis}
                formatTooltipValue={formatTip}
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
