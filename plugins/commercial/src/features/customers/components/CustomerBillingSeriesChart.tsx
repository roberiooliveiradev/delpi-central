import { useMemo, useState } from "react";
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
  CommercialMultiSelectField,
  CommercialSectionCard,
  CommercialStateBanner,
  CommercialTabularExportButtons,
  cmEmptyStateClassNames,
  useChartGranularitySelection,
} from "../../../app/commercialUi";
import { CUSTOMER_BILLING_CONTENT } from "../../../content/customerBillingContent";
import { CM_HELP } from "../../../content/helpTooltips";
import {
  PeriodCompareControls,
  type CompareYearsCount,
} from "../../analytics/components/PeriodCompareControls";
import { formatCurrency } from "../../../utils/format";
import { buildBillingSeriesExportPayload } from "../utils/billingSeriesExportBuilders";
import { validateBillingPeriod } from "../billing/utils/billingPeriod";
import { useCustomerBillingSeries } from "../hooks/useCustomerBillingSeries";
import type { CustomerSummary } from "../types/customerSummary";
import {
  BILLING_SERIES_GRANULARITY_OPTIONS,
  DEFAULT_BILLING_SERIES_PRESET,
  allowedBillingSeriesGranularities,
  billingSeriesPresetLabel,
  periodRangeFromBillingPreset,
  type BillingSeriesPeriodPreset,
} from "../utils/billingSeriesPeriod";

/** Mesma altura do gráfico ROL do dashboard comercial. */
const CHART_HEIGHT = 320;

/** Accent do Portal — acompanha tema claro/escuro. */
const SERIES_COLOR = "var(--cm-accent)";
const PRIOR_SERIES_COLOR = "var(--chart-3, #94a3b8)";
const PRIOR_2_COLOR = "var(--chart-4, #64748b)";
const PRIOR_3_COLOR = "var(--chart-5, #475569)";

type CustomerBillingSeriesChartProps = {
  customers: CustomerSummary[];
  /** Quando false, não dispara fetch (painel oculto). Default true. */
  active?: boolean;
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
 * Faturamento da carteira — período (paridade Overview) + YoY opcional.
 */
export function CustomerBillingSeriesChart({
  customers,
  active = true,
}: CustomerBillingSeriesChartProps) {
  const defaultRange = periodRangeFromBillingPreset(DEFAULT_BILLING_SERIES_PRESET);
  const [preset, setPreset] = useState<BillingSeriesPeriodPreset>(
    DEFAULT_BILLING_SERIES_PRESET,
  );
  const [customStart, setCustomStart] = useState(defaultRange.startDate);
  const [customEnd, setCustomEnd] = useState(defaultRange.endDate);
  const { preferences, setPreferences, setChartType } = usePersistedChartPreferences({
    storageKey: "commercial:customers:billing-series",
    defaults: { chartType: "column", compareYears: 0, showTrend: false },
    allowedChartTypes: TIME_MULTI_SERIES_TYPES,
  });
  const compareYears = (preferences.compareYears ?? 0) as CompareYearsCount;
  const setCompareYears = (value: CompareYearsCount) =>
    setPreferences({ compareYears: value });
  const showTrend = Boolean(preferences.showTrend);
  const chartType = preferences.chartType ?? "column";

  const range =
    preset === "custom"
      ? { startDate: customStart, endDate: customEnd }
      : periodRangeFromBillingPreset(preset);
  const periodError =
    preset === "custom" ? validateBillingPeriod(range.startDate, range.endDate) : null;
  const queryEnabled = active && !periodError;
  const allowedGrains = allowedBillingSeriesGranularities(
    range.startDate,
    range.endDate,
  );
  const { granularity, setGranularity } = useChartGranularitySelection(
    range.startDate,
    range.endDate,
  );
  const effectiveGrain = allowedGrains.includes(granularity)
    ? granularity
    : (allowedGrains[0] ?? "month");

  const yoyActive = compareYears >= 1 && Boolean(range.startDate && range.endDate);

  const {
    selectedKeys,
    setSelectedKeys,
    customerOptions,
    points,
    loading,
    error,
    totalValue,
    coverage,
    reload,
  } = useCustomerBillingSeries(customers, {
    enabled: queryEnabled,
    startDate: range.startDate,
    endDate: range.endDate,
    granularity: effectiveGrain,
    compareYears: yoyActive ? compareYears : 0,
  });

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
    if (compareYears >= 1) {
      list.push({
        dataKey: "faturamento_prior",
        name: "Ano ant.",
        fill: PRIOR_SERIES_COLOR,
      });
    }
    if (compareYears >= 2) {
      list.push({
        dataKey: "faturamento_prior_2",
        name: "−2 anos",
        fill: PRIOR_2_COLOR,
      });
    }
    if (compareYears >= 3) {
      list.push({
        dataKey: "faturamento_prior_3",
        name: "−3 anos",
        fill: PRIOR_3_COLOR,
      });
    }
    return list;
  }, [compareYears]);

  const hasValues = chartData.some(
    (point) =>
      point.faturamento > 0 ||
      (yoyActive &&
        ((point.faturamento_prior != null && point.faturamento_prior > 0) ||
          (point.faturamento_prior_2 != null && point.faturamento_prior_2 > 0) ||
          (point.faturamento_prior_3 != null && point.faturamento_prior_3 > 0))),
  );
  const filterLabel = billingFilterLabel(selectedKeys, customerOptions);
  const periodLabel = billingSeriesPresetLabel(preset);
  const isAllCustomers = selectedKeys.length === 0;

  return (
    <div className="cm-billing-series-chart">
      <CommercialSectionCard
        title={`Faturamento — ${periodLabel}`}
        hint={CM_HELP.customers.billingSeries}
        subtitle={
          loading
            ? "Atualizando série…"
            : hasValues
              ? `Total no período · ${filterLabel}: ${formatCurrency(totalValue)}`
              : undefined
        }
        actions={
          <div className="cm-billing-series-chart__customer-filter">
            <CommercialMultiSelectField
              label="Cliente"
              hint={CM_HELP.customerDetail.billingSeriesCustomer}
              options={customerOptions.map((customer) => ({
                value: customer.key,
                label: `${customer.nome} (${customer.codigo}/${customer.loja})`,
              }))}
              selectedValues={selectedKeys}
              onChange={setSelectedKeys}
              emptyLabel="Todos os clientes"
              searchable
              disabled={loading && customerOptions.length === 0}
            />
          </div>
        }
      >
      <div className="cm-billing-series-chart__controls">
        <PeriodCompareControls
          idPrefix="customers-billing"
          preset={preset}
          onPresetChange={setPreset}
          customStart={customStart}
          customEnd={customEnd}
          onCustomStartChange={setCustomStart}
          onCustomEndChange={setCustomEnd}
          compareYears={compareYears}
          onCompareYearsChange={setCompareYears}
          trailing={
            periodError ? undefined : (
              <CommercialChartToolbar
                granularity={effectiveGrain}
                onGranularityChange={setGranularity}
                options={BILLING_SERIES_GRANULARITY_OPTIONS}
                modes={allowedGrains}
                granularityHelp={CM_HELP.customers.billingSeriesGrain}
              />
            )
          }
        />
        {periodError ? (
          <CommercialStateBanner>{periodError}</CommercialStateBanner>
        ) : null}
      </div>
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
            typeToggle={
              <ChartTypeSegmentToggle
                family="time_multi_series"
                value={chartType}
                onChange={setChartType}
                idPrefix="customers-billing-type"
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
                      title: `Faturamento — ${periodLabel}`,
                      compareYears,
                    }),
                  });
                }}
              />
            }
            overlays={
              <NativeCheckboxControl
                id="customers-billing-trend"
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
              showLegend={yoyActive || showTrend}
              trendSeriesName={CUSTOMER_BILLING_CONTENT.trendLineSeriesName}
              formatY={formatChartCurrency}
              formatTooltipValue={formatCurrency}
            />
          </ChartViewShell>
        </>
      )}
      </CommercialSectionCard>
    </div>
  );
}
