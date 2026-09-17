import { useMemo } from "react";
import {
  ChartOverlayOptionsPopover,
  ChartSeriesColorsPopover,
  ChartTypeSegmentToggle,
  ChartViewShell,
  EmptyState,
  MultiTypeSeriesChart,
  TIME_MULTI_SERIES_TYPES,
  applySeriesFillPreferences,
  buildCompareYearsOverlayOptions,
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
} from "../../../app/commercialUi";
import { ANALYTICS_CONTENT } from "../../../content/analyticsContent";
import { CUSTOMER_BILLING_CONTENT } from "../../../content/customerBillingContent";
import { CM_HELP } from "../../../content/helpTooltips";
import {
  appendBillingNatureContext,
  billingNatureShortLabel,
  type PortfolioBillingAmountNature,
} from "../../../content/billingNature";
import {
  billingMetricShortLabel,
  formatChartMetricValue,
  formatMetricTotal,
  quantitySeriesName,
  includesQuantityMetric,
  includesValueMetric,
  type PortfolioBillingMetric,
} from "../../../content/billingMetric";
import {
  type CompareYearsCount,
} from "../../analytics/components/PeriodCompareControls";
import { resolveCalendarBucketFraction } from "../../../utils/linearTrendSeries";
import { buildBillingSeriesExportPayload } from "../utils/billingSeriesExportBuilders";
import { useCustomerBillingSeries } from "../hooks/useCustomerBillingSeries";
import type { CustomerSummary } from "../types/customerSummary";
import type { PortfolioBillingWorkspaceFilters } from "../hooks/usePortfolioBillingWorkspaceFilters";
import {
  BILLING_SERIES_GRANULARITY_OPTIONS,
  allowedBillingSeriesGranularities,
  billingSeriesPresetLabel,
} from "../utils/billingSeriesPeriod";

/** Mesma altura do gráfico ROL do dashboard comercial. */
const CHART_HEIGHT = 320;

/** Accent do Portal — acompanha tema claro/escuro. */
const SERIES_COLOR = "var(--cm-accent)";
/** Distinta de `--chart-2` (tom do primary no Portal) para não parecer a mesma coluna. */
const QUANTITY_SERIES_COLOR = "var(--cm-chart-quantity, #ea580c)";
const QUANTITY_PRIOR_COLOR = "var(--cm-chart-quantity-prior, #fdba74)";
const QUANTITY_PRIOR_2_COLOR = "var(--cm-chart-quantity-prior-2, #fed7aa)";
const QUANTITY_PRIOR_3_COLOR = "var(--cm-chart-quantity-prior-3, #ffedd5)";
const PRIOR_SERIES_COLOR = "var(--chart-3, #94a3b8)";
const PRIOR_2_COLOR = "var(--chart-4, #64748b)";
const PRIOR_3_COLOR = "var(--chart-5, #475569)";

type CustomerBillingSeriesChartProps = {
  customers: CustomerSummary[];
  filters: PortfolioBillingWorkspaceFilters;
  /** Quando false, não dispara fetch (painel oculto). Default true. */
  active?: boolean;
  billingNature?: PortfolioBillingAmountNature;
  billingMetric?: PortfolioBillingMetric;
};

function billingFilterLabel(
  selectedKeys: string[],
  customerOptions: Array<{ key: string; nome: string }>,
): string {
  if (selectedKeys.length === 0) return "Toda a carteira";
  if (selectedKeys.length === 1) {
    return customerOptions.find((c) => c.key === selectedKeys[0])?.nome ?? "Cliente";
  }
  return `${selectedKeys.length} clientes`;
}

/**
 * Faturamento da carteira — período e clientes vêm do workspace compartilhado.
 */
export function CustomerBillingSeriesChart({
  customers,
  filters,
  active = true,
  billingNature = "gross",
  billingMetric = "value",
}: CustomerBillingSeriesChartProps) {
  const { preferences, setPreferences, setChartType } = usePersistedChartPreferences({
    storageKey: "commercial:customers:billing-series",
    defaults: {
      chartType: "column",
      compareYears: 0,
      showTrend: false,
      incompleteBucketMode: "exclude",
    },
    allowedChartTypes: TIME_MULTI_SERIES_TYPES,
  });
  const compareYears = (preferences.compareYears ?? 0) as CompareYearsCount;
  const showTrend = Boolean(preferences.showTrend);
  const incompleteBucketMode =
    preferences.incompleteBucketMode === "weightByFraction"
      ? "weightByFraction"
      : "exclude";
  const chartType = preferences.chartType ?? "column";

  const overlayOptions = useMemo((): ChartOverlayOption[] => {
    const compare = buildCompareYearsOverlayOptions({
      compareYears,
      onCompareYearsChange: (value) => setPreferences({ compareYears: value }),
      labels: {
        priorYear: ANALYTICS_CONTENT.overview.comparePriorYear,
        plus2: ANALYTICS_CONTENT.overview.compareYearsPlus2,
        plus3: ANALYTICS_CONTENT.overview.compareYearsPlus3,
        priorYearSummary: ANALYTICS_CONTENT.overview.compareYearsDepth1,
        plus2Summary: ANALYTICS_CONTENT.overview.compareYearsDepth2,
        plus3Summary: ANALYTICS_CONTENT.overview.compareYearsDepth3,
        priorYearHint: CM_HELP.customers.billingSeriesYoy,
        plus2Hint: "Sobrepõe também o período deslocado −2 anos.",
        plus3Hint: "Sobrepõe também o período deslocado −3 anos.",
      },
    });
    return [
      ...compare,
      {
        id: "trend",
        label: CUSTOMER_BILLING_CONTENT.showTrendLine,
        summaryLabel: CUSTOMER_BILLING_CONTENT.showTrendLine,
        checked: showTrend,
        onChange: (checked) => setPreferences({ showTrend: checked }),
        hint: CM_HELP.customerDetail.billingSeriesTrend,
        hintAriaLabel: "Ajuda: linha de tendência",
      },
      {
        id: "trend-weight",
        label: "Ponderar período parcial",
        summaryLabel: "Tendência ponderada",
        hint: CM_HELP.customers.billingTrendIncomplete,
        hintAriaLabel: "Ajuda: tendência em período parcial",
        checked: incompleteBucketMode === "weightByFraction",
        onChange: (checked) =>
          setPreferences({
            incompleteBucketMode: checked ? "weightByFraction" : "exclude",
          }),
        disabled: !showTrend,
      },
    ];
  }, [compareYears, incompleteBucketMode, setPreferences, showTrend]);

  const queryEnabled = active && !filters.periodError;
  const allowedGrains = allowedBillingSeriesGranularities(
    filters.startDate,
    filters.endDate,
  );
  const { granularity, setGranularity } = useChartGranularitySelection(
    filters.startDate,
    filters.endDate,
  );
  const effectiveGrain = allowedGrains.includes(granularity)
    ? granularity
    : (allowedGrains[0] ?? "month");

  const yoyActive = compareYears >= 1 && Boolean(filters.startDate && filters.endDate);

  const {
    points,
    loading,
    error,
    totalValue,
    totalQuantity,
    quantityUnit,
    quantityMixedUnits,
    coverage,
    reload,
  } = useCustomerBillingSeries(customers, {
    enabled: queryEnabled,
    startDate: filters.startDate,
    endDate: filters.endDate,
    granularity: effectiveGrain,
    compareYears: yoyActive ? compareYears : 0,
    nature: billingNature,
    metric: billingMetric,
    productCodes: filters.selectedProductCodes,
    productGroups: filters.selectedProductGroups,
    market: filters.marketParam,
    selectedKeys: filters.selectedCustomerKeys,
    onSelectedKeysChange: filters.setSelectedCustomerKeys,
  });

  const showValue = includesValueMetric(billingMetric);
  const showQuantity = includesQuantityMetric(billingMetric);

  const chartData = useMemo(
    () =>
      points.map((point) => ({
        periodo: point.label,
        faturamento: Number(point.value) || 0,
        faturamento_prior:
          point.value_prior == null ? null : Number(point.value_prior) || 0,
        faturamento_prior_2:
          point.value_prior_2 == null ? null : Number(point.value_prior_2) || 0,
        faturamento_prior_3:
          point.value_prior_3 == null ? null : Number(point.value_prior_3) || 0,
        quantidade: Number(point.quantity) || 0,
        quantidade_prior:
          point.quantity_prior == null ? null : Number(point.quantity_prior) || 0,
        quantidade_prior_2:
          point.quantity_prior_2 == null ? null : Number(point.quantity_prior_2) || 0,
        quantidade_prior_3:
          point.quantity_prior_3 == null ? null : Number(point.quantity_prior_3) || 0,
        _bucketFraction: resolveCalendarBucketFraction(
          point.date_start,
          point.date_end,
        ),
      })),
    [points],
  );

  const quantityLabel = quantitySeriesName(quantityUnit, quantityMixedUnits);
  const quantityAxisUnit = quantityMixedUnits ? null : quantityUnit;
  const baseBars = useMemo((): MultiTypeSeriesSpec[] => {
    const valueName = appendBillingNatureContext("Faturamento", billingNature);
    const list: MultiTypeSeriesSpec[] = [];
    if (showValue) {
      list.push({
        dataKey: "faturamento",
        name: valueName,
        fill: SERIES_COLOR,
        trendSource: true,
      });
    }
    if (showQuantity && billingMetric === "quantity") {
      list.push({
        dataKey: "faturamento",
        name: quantityLabel,
        fill: SERIES_COLOR,
        trendSource: true,
      });
    }
    if (showQuantity && billingMetric === "both") {
      list.push({
        dataKey: "quantidade",
        name: quantityLabel,
        fill: QUANTITY_SERIES_COLOR,
        axis: "secondary",
      });
    }
    if (showValue && compareYears >= 1) {
      list.push({
        dataKey: "faturamento_prior",
        name: "Ano ant.",
        fill: PRIOR_SERIES_COLOR,
      });
    }
    if (showQuantity && billingMetric === "both" && compareYears >= 1) {
      list.push({
        dataKey: "quantidade_prior",
        name: "Qtd ano ant.",
        fill: QUANTITY_PRIOR_COLOR,
        axis: "secondary",
      });
    }
    if (showValue && compareYears >= 2) {
      list.push({
        dataKey: "faturamento_prior_2",
        name: "−2 anos",
        fill: PRIOR_2_COLOR,
      });
    }
    if (showQuantity && billingMetric === "both" && compareYears >= 2) {
      list.push({
        dataKey: "quantidade_prior_2",
        name: "Qtd −2 anos",
        fill: QUANTITY_PRIOR_2_COLOR,
        axis: "secondary",
      });
    }
    if (showValue && compareYears >= 3) {
      list.push({
        dataKey: "faturamento_prior_3",
        name: "−3 anos",
        fill: PRIOR_3_COLOR,
      });
    }
    if (showQuantity && billingMetric === "both" && compareYears >= 3) {
      list.push({
        dataKey: "quantidade_prior_3",
        name: "Qtd −3 anos",
        fill: QUANTITY_PRIOR_3_COLOR,
        axis: "secondary",
      });
    }
    return list;
  }, [billingMetric, billingNature, compareYears, quantityLabel, showQuantity, showValue]);

  const bars = useMemo(
    () => applySeriesFillPreferences(baseBars, preferences.seriesFills),
    [baseBars, preferences.seriesFills],
  );

  const hasValues = chartData.some(
    (point) =>
      point.faturamento > 0 ||
      point.quantidade > 0 ||
      (yoyActive &&
        ((point.faturamento_prior != null && point.faturamento_prior > 0) ||
          (point.faturamento_prior_2 != null && point.faturamento_prior_2 > 0) ||
          (point.faturamento_prior_3 != null && point.faturamento_prior_3 > 0) ||
          (point.quantidade_prior != null && point.quantidade_prior > 0) ||
          (point.quantidade_prior_2 != null && point.quantidade_prior_2 > 0) ||
          (point.quantidade_prior_3 != null && point.quantidade_prior_3 > 0))),
  );
  const filterLabel = billingFilterLabel(
    filters.selectedCustomerKeys,
    filters.customerOptions,
  );
  const periodLabel = billingSeriesPresetLabel(filters.preset);
  const natureLabel = billingNatureShortLabel(billingNature);
  const metricLabel = billingMetricShortLabel(billingMetric);
  const chartTitle =
    billingMetric === "quantity"
      ? `${quantityLabel} — ${periodLabel}`
      : billingMetric === "both"
        ? appendBillingNatureContext(`Faturamento e quantidade — ${periodLabel}`, billingNature)
        : appendBillingNatureContext(`Faturamento — ${periodLabel}`, billingNature);
  const isAllCustomers = filters.selectedCustomerKeys.length === 0;
  const formatValue = (value: number) =>
    formatChartMetricValue(
      value,
      billingMetric === "quantity" ? "quantity" : "value",
      billingMetric === "quantity" ? quantityAxisUnit : undefined,
    );
  const formatQuantityAxis = (value: number) =>
    formatChartMetricValue(value, "quantity", quantityAxisUnit);
  const totalLabel =
    billingMetric === "both"
      ? `${formatMetricTotal(totalValue, "value")} · ${formatMetricTotal(totalQuantity, "quantity", quantityUnit, quantityMixedUnits)}`
      : formatMetricTotal(
          totalValue,
          billingMetric === "quantity" ? "quantity" : "value",
          billingMetric === "quantity" ? quantityUnit : undefined,
          billingMetric === "quantity" ? quantityMixedUnits : undefined,
        );

  return (
    <div className="cm-billing-series-chart">
      <CommercialSectionCard
        title={chartTitle}
        hint={CM_HELP.customers.billingSeries}
        subtitle={
          loading
            ? "Atualizando série…"
            : hasValues
              ? `Total no período · ${filterLabel}: ${totalLabel} · ${metricLabel}${
                  showValue ? ` · ${natureLabel}` : ""
                }`
              : undefined
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
          defaultMessage={
            isAllCustomers
              ? `Sem faturamento registrado em ${periodLabel.toLocaleLowerCase("pt-BR")} para a carteira.`
              : `Sem faturamento registrado em ${periodLabel.toLocaleLowerCase("pt-BR")} para o filtro de clientes.`
          }
        />
      ) : (
        <>
          {error ? (
            <CommercialStateBanner>
              <p>{error} Cobertura: {coverage.covered}/{coverage.total}.</p>
              <CommercialActionButton variant="ghost" onClick={reload} disabled={loading}>
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
              <CommercialChartGranularityToggle
                value={effectiveGrain}
                onChange={setGranularity}
                options={BILLING_SERIES_GRANULARITY_OPTIONS}
                modes={allowedGrains}
                idPrefix="customers-billing"
              />
            }
            overlays={
              <ChartOverlayOptionsPopover
                idPrefix="customers-billing-overlays"
                portalScopeClassName="dashboard-commercial"
                panelTitle={ANALYTICS_CONTENT.overview.chartOverlaysPanelTitle}
                emptySummaryLabel={ANALYTICS_CONTENT.overview.chartOverlaysEmpty}
                options={overlayOptions}
              />
            }
            seriesColors={
              <ChartSeriesColorsPopover
                idPrefix="customers-billing-colors"
                portalScopeClassName="dashboard-commercial"
                series={bars}
                values={preferences.seriesFills}
                summaryLabel={ANALYTICS_CONTENT.overview.chartSeriesColorsEmpty}
                panelTitle={ANALYTICS_CONTENT.overview.chartSeriesColorsPanelTitle}
                triggerAriaLabel={ANALYTICS_CONTENT.overview.chartSeriesColorsTriggerAria}
                resetLabel={ANALYTICS_CONTENT.overview.chartSeriesColorsReset}
                onChange={(dataKey, color) =>
                  setPreferences((prev) => ({
                    ...prev,
                    seriesFills: { ...(prev.seriesFills ?? {}), [dataKey]: color },
                  }))
                }
                onReset={() =>
                  setPreferences((prev) => ({ ...prev, seriesFills: undefined }))
                }
              />
            }
            typeToggle={
              <ChartTypeSegmentToggle
                family="time_multi_series"
                value={chartType}
                onChange={setChartType}
                idPrefix="customers-billing-type"
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
                      compareYears,
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
              showTrend={showTrend}
              incompleteBucketMode={incompleteBucketMode}
              showLegend={yoyActive || showTrend || billingMetric === "both"}
              trendSeriesName={CUSTOMER_BILLING_CONTENT.trendLineSeriesName}
              formatY={formatValue}
              formatYSecondary={
                billingMetric === "both" ? formatQuantityAxis : undefined
              }
              secondaryDataKeys={
                billingMetric === "both"
                  ? [
                      "quantidade",
                      ...(compareYears >= 1 ? ["quantidade_prior"] : []),
                      ...(compareYears >= 2 ? ["quantidade_prior_2"] : []),
                      ...(compareYears >= 3 ? ["quantidade_prior_3"] : []),
                    ]
                  : undefined
              }
              formatTooltipValue={
                billingMetric === "both" ? undefined : formatValue
              }
            />
          </ChartViewShell>
        </>
      )}
      </CommercialSectionCard>
    </div>
  );
}
