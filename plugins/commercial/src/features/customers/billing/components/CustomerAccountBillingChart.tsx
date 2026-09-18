import { useMemo } from "react";
import {
  ChartOverlayOptionsPopover,
  ChartSeriesColorsPopover,
  ChartTypeSegmentToggle,
  ChartViewShell,
  EmptyState,
  MultiTypeSeriesChart,
  TIME_MULTI_SERIES_TYPES,
  applySeriesViewPreferences,
  buildChartSeriesConfigItems,
  omitRecordKey,
  patchSeriesTrendStyle,
  resetSeriesViewPreferences,
  runTabularExport,
  seriesViewHasOverrides,
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
  quantitySeriesName,
  type PortfolioBillingMetric,
} from "../../../../content/billingMetric";
import { CUSTOMER_BILLING_CONTENT } from "../../../../content/customerBillingContent";
import { CM_HELP } from "../../../../content/helpTooltips";
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
  const incompleteBucketMode =
    preferences.incompleteBucketMode === "weightByFraction"
      ? "weightByFraction"
      : "exclude";
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

  const { points, loading, error, totalValue, quantityUnit, quantityMixedUnits, coverage, reload } =
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

  const quantityAxisUnit = quantityMixedUnits ? null : quantityUnit;
  const seriesName =
    billingMetric === "quantity"
      ? quantitySeriesName(quantityUnit, quantityMixedUnits)
      : "Faturamento";
  const baseBars = useMemo((): MultiTypeSeriesSpec[] => {
    const list: MultiTypeSeriesSpec[] = [
      {
        dataKey: "faturamento",
        name: seriesName,
        fill: SERIES_COLOR,
      },
    ];
    if (comparePriorYear) {
      list.push({
        dataKey: "faturamento_prior",
        name: "Ano ant.",
        fill: PRIOR_SERIES_COLOR,
        trendApplyIncompleteBucket: false,
      });
    }
    return list;
  }, [comparePriorYear, seriesName]);

  const bars = useMemo(
    () => applySeriesViewPreferences(baseBars, preferences),
    [baseBars, preferences],
  );
  const anyTrend = bars.some((entry) => entry.trendSource);
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
    ];
  }, [comparePriorYear, onComparePriorYearChange]);
  const seriesConfigItems = useMemo(
    () => buildChartSeriesConfigItems(baseBars, preferences),
    [baseBars, preferences],
  );

  const hasValues = chartData.some(
    (point) =>
      point.faturamento > 0 ||
      (comparePriorYear &&
        point.faturamento_prior != null &&
        point.faturamento_prior > 0),
  );

  const chartTitle =
    billingMetric === "quantity"
      ? `${quantitySeriesName(quantityUnit, quantityMixedUnits)} no período`
      : "Faturamento no período";
  const metricLabel = billingMetricShortLabel(billingMetric);
  const totalLabel = formatMetricTotal(
    totalValue,
    billingMetric,
    billingMetric === "quantity" ? quantityUnit : undefined,
    billingMetric === "quantity" ? quantityMixedUnits : undefined,
  );
  const formatAxis = (value: number) =>
    formatChartMetricValue(
      value,
      billingMetric,
      billingMetric === "quantity" ? quantityAxisUnit : undefined,
    );
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
              seriesColorsLabel={ANALYTICS_CONTENT.overview.chartSeriesColorsLabel}
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
              seriesColors={
                <ChartSeriesColorsPopover
                  idPrefix="account-billing-colors"
                  portalScopeClassName="dashboard-commercial"
                  series={seriesConfigItems}
                  values={preferences.seriesFills}
                  hasOverrides={seriesViewHasOverrides(preferences)}
                  summaryLabel={ANALYTICS_CONTENT.overview.chartSeriesColorsEmpty}
                  panelTitle={ANALYTICS_CONTENT.overview.chartSeriesColorsPanelTitle}
                  triggerAriaLabel={ANALYTICS_CONTENT.overview.chartSeriesColorsTriggerAria}
                  resetLabel={ANALYTICS_CONTENT.overview.chartSeriesColorsReset}
                  resetSeriesLabel={ANALYTICS_CONTENT.overview.chartSeriesColorsResetSeries}
                  onChange={(dataKey, color) =>
                    setPreferences((prev) => ({
                      ...prev,
                      seriesFills: { ...(prev.seriesFills ?? {}), [dataKey]: color },
                    }))
                  }
                  onVisibleChange={(dataKey, visible) =>
                    setPreferences((prev) => ({
                      ...prev,
                      hiddenSeries: visible
                        ? omitRecordKey(prev.hiddenSeries, dataKey)
                        : { ...(prev.hiddenSeries ?? {}), [dataKey]: true },
                    }))
                  }
                  onTrendChange={(dataKey, enabled) =>
                    setPreferences((prev) => ({
                      ...prev,
                      seriesTrend: { ...(prev.seriesTrend ?? {}), [dataKey]: enabled },
                    }))
                  }
                  incompleteBucketWeighted={
                    incompleteBucketMode === "weightByFraction"
                  }
                  onIncompleteBucketWeightChange={(weighted) =>
                    setPreferences({
                      incompleteBucketMode: weighted
                        ? "weightByFraction"
                        : "exclude",
                    })
                  }
                  incompleteBucketWeightHint={CM_HELP.customers.billingTrendIncomplete}
                  incompleteBucketWeightHintAriaLabel="Ajuda: tendência em período parcial"
                  onTrendStyleChange={(dataKey, style) =>
                    setPreferences((prev) => ({
                      ...prev,
                      seriesTrendStyles: patchSeriesTrendStyle(
                        prev.seriesTrendStyles,
                        dataKey,
                        style,
                      ),
                    }))
                  }
                  onResetSeries={(dataKey) =>
                    setPreferences((prev) => resetSeriesViewPreferences(prev, dataKey))
                  }
                  onReset={() =>
                    setPreferences((prev) => resetSeriesViewPreferences(prev))
                  }
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
                        metric: billingMetric,
                        unit: quantityUnit,
                        mixedUnits: quantityMixedUnits,
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
                showTrend={bars.some((entry) => entry.trendSource)}
                incompleteBucketMode={incompleteBucketMode}
                showLegend={comparePriorYear || anyTrend}
                trendSeriesName={CUSTOMER_BILLING_CONTENT.trendLineSeriesName}
                formatY={formatAxis}
                formatTooltipValue={formatAxis}
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
