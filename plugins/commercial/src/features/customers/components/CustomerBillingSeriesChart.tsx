import { useId, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { EmptyState, SegmentToggle } from "@delpi/plugin-ui/index";

import {
  CommercialActionButton,
  CommercialChartToolbar,
  CommercialDateField,
  CommercialFilterBarShell,
  CommercialMultiSelectField,
  CommercialSectionCard,
  CommercialStateBanner,
  UI_PREFIX,
  cmEmptyStateClassNames,
  useChartGranularitySelection,
} from "../../../app/commercialUi";
import { CM_HELP } from "../../../content/helpTooltips";
import { formatCurrency } from "../../../utils/format";
import { validateBillingPeriod } from "../billing/utils/billingPeriod";
import { useCustomerBillingSeries } from "../hooks/useCustomerBillingSeries";
import { useLazyBillingSeriesActivation } from "../hooks/useLazyBillingSeriesActivation";
import type { CustomerSummary } from "../types/customerSummary";
import {
  BILLING_SERIES_GRANULARITY_OPTIONS,
  BILLING_SERIES_PRESET_OPTIONS,
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
 * Faturamento da carteira — período e granularidade reais via API existente.
 */
export function CustomerBillingSeriesChart({ customers }: CustomerBillingSeriesChartProps) {
  const gradientId = useId().replace(/:/g, "");
  const { anchorRef, open, setOpen, enabled } = useLazyBillingSeriesActivation();
  const defaultRange = periodRangeFromBillingPreset(DEFAULT_BILLING_SERIES_PRESET);
  const [preset, setPreset] = useState<BillingSeriesPeriodPreset>(
    DEFAULT_BILLING_SERIES_PRESET,
  );
  const [customStart, setCustomStart] = useState(defaultRange.startDate);
  const [customEnd, setCustomEnd] = useState(defaultRange.endDate);

  const range =
    preset === "custom"
      ? { startDate: customStart, endDate: customEnd }
      : periodRangeFromBillingPreset(preset);
  const periodError =
    preset === "custom" ? validateBillingPeriod(range.startDate, range.endDate) : null;
  const queryEnabled = enabled && !periodError;
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
  });

  const chartData = useMemo(
    () =>
      points.map((point) => ({
        periodo: point.label,
        faturamento: Number(point.value) || 0,
      })),
    [points],
  );

  const hasValues = chartData.some((point) => point.faturamento > 0);
  const filterLabel = billingFilterLabel(selectedKeys, customerOptions);
  const periodLabel = billingSeriesPresetLabel(preset);
  const isAllCustomers = selectedKeys.length === 0;

  return (
    <div ref={anchorRef} className="cm-billing-series-chart">
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
        collapsible
        open={open}
        onOpenChange={setOpen}
        actions={
          open ? (
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
          ) : undefined
        }
      >
      <div className="cm-billing-series-chart__controls">
        <CommercialFilterBarShell
          embedded
          layout={preset === "custom" ? "grid" : "inline"}
          ariaLabel={CM_HELP.customers.billingSeriesPeriod}
          leading={
            <SegmentToggle
              prefix={UI_PREFIX}
              ariaLabel={CM_HELP.customers.billingSeriesPeriod}
              idPrefix="customers-billing-period"
              value={preset}
              onChange={setPreset}
              options={BILLING_SERIES_PRESET_OPTIONS.map((item) => ({
                value: item.id,
                label: item.label,
              }))}
            />
          }
        >
          {preset === "custom" ? (
            <>
              <CommercialDateField
                label="Data inicial"
                hint={CM_HELP.customerDetail.billingSeriesDateStart}
                value={customStart}
                onChange={setCustomStart}
              />
              <CommercialDateField
                label="Data final"
                hint={CM_HELP.customerDetail.billingSeriesDateEnd}
                value={customEnd}
                onChange={setCustomEnd}
              />
            </>
          ) : null}
        </CommercialFilterBarShell>
        {periodError ? (
          <CommercialStateBanner>{periodError}</CommercialStateBanner>
        ) : (
          <CommercialChartToolbar
            granularity={effectiveGrain}
            onGranularityChange={setGranularity}
            options={BILLING_SERIES_GRANULARITY_OPTIONS}
            modes={allowedGrains}
            granularityHelp={CM_HELP.customers.billingSeriesGrain}
          />
        )}
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
        </>
      )}
      </CommercialSectionCard>
    </div>
  );
}
