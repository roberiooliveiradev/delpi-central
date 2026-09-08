import { useMemo } from "react";
import {
  ChartCard,
  ChartOverlayOptionsPopover,
  ChartTypeSegmentToggle,
  ChartViewShell,
  chartCardBemClasses,
  EmptyState,
  MultiTypeSeriesChart,
  PERIOD_COMPARE_TYPES,
  runTabularExport,
  usePersistedChartPreferences,
  type ChartOverlayOption,
} from "@delpi/plugin-ui/index";

import {
  CommercialSectionHintLabel,
  CommercialSegmentToggle,
  CommercialSelectField,
  CommercialTabularExportButtons,
  cmEmptyStateClassNames,
} from "../../../app/commercialUi";
import { ANALYTICS_CONTENT } from "../../../content/analyticsContent";
import {
  BILLING_METRIC_CONTENT,
  formatChartMetricValue,
  formatMetricTotal,
  type PortfolioBillingMetric,
} from "../../../content/billingMetric";
import { CUSTOMER_BILLING_CONTENT } from "../../../content/customerBillingContent";
import { CM_HELP } from "../../../content/helpTooltips";
import { formatCurrency, formatQuantity } from "../../../utils/format";
import { buildPurchaseEvolutionExportPayload } from "../utils/billingSeriesExportBuilders";
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
  billingMetric?: PortfolioBillingMetric;
  onBillingMetricChange?: (metric: PortfolioBillingMetric) => void;
};

function parseWindowMonths(value: string): PurchaseEvolutionWindowMonths {
  return value === "6" ? 6 : 12;
}

export function CustomerPurchaseEvolutionChart({
  points,
  loading,
  error,
  windowMonths,
  onWindowMonthsChange,
  billingMetric = "value",
  onBillingMetricChange,
}: CustomerPurchaseEvolutionChartProps) {
  const { preferences, setPreferences, setChartType } = usePersistedChartPreferences({
    storageKey: "commercial:account:purchase-evolution",
    defaults: { chartType: "column", showTrend: false },
    allowedChartTypes: PERIOD_COMPARE_TYPES,
  });
  const showTrend = Boolean(preferences.showTrend);
  const chartType = preferences.chartType ?? "column";

  const overlayOptions = useMemo((): ChartOverlayOption[] => {
    return [
      {
        id: "trend",
        label: CUSTOMER_BILLING_CONTENT.showTrendLine,
        checked: showTrend,
        onChange: (checked) => setPreferences({ showTrend: checked }),
        hint: CM_HELP.customerDetail.billingSeriesTrend,
        hintAriaLabel: "Ajuda: linha de tendência",
      },
    ];
  }, [setPreferences, showTrend]);

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

  const chartData = useMemo(
    () =>
      points.map((point) => ({
        periodo: point.periodo,
        atual: Number(point.atual) || 0,
        anterior: Number(point.anterior) || 0,
      })),
    [points],
  );

  const formatAxis = (value: number) => formatChartMetricValue(value, billingMetric);
  const formatTip =
    billingMetric === "quantity" ? formatQuantity : formatCurrency;

  const bars = useMemo(
    () => [
      {
        dataKey: "atual",
        name: `Período atual · ${formatMetricTotal(totals.atual, billingMetric)}`,
        fill: COLOR_CURRENT,
        trendSource: true,
      },
      {
        dataKey: "anterior",
        name: `Período anterior · ${formatMetricTotal(totals.anterior, billingMetric)}`,
        fill: COLOR_PRIOR,
      },
    ],
    [billingMetric, totals.atual, totals.anterior],
  );

  const emptyMessage =
    billingMetric === "quantity"
      ? windowMonths === 6
        ? "Sem quantidade fornecida nos últimos 12 meses para este cliente."
        : "Sem quantidade fornecida nos últimos 24 meses para este cliente."
      : windowMonths === 6
        ? "Sem faturamento registrado nos últimos 12 meses para este cliente."
        : "Sem faturamento registrado nos últimos 24 meses para este cliente.";

  const chartTitle =
    billingMetric === "quantity"
      ? "Evolução de fornecimento (quantidade)"
      : "Evolução de compras";

  return (
    <ChartCard
      title={chartTitle}
      titleHint={CM_HELP.customerDetail.purchaseEvolution}
      hint={CM_HELP.customerDetail.purchaseEvolutionComparison}
      classNames={CHART_CLASSES}
      className="cm-purchase-evolution"
      headerActions={
        <div className="cm-purchase-evolution__header-actions">
          {onBillingMetricChange ? (
            <div className="cm-field">
              <CommercialSectionHintLabel
                label="Métrica"
                hint={CM_HELP.customers.billingMetric}
              />
              <CommercialSegmentToggle
                ariaLabel={CM_HELP.customers.billingMetric}
                idPrefix="purchase-evolution-metric"
                value={billingMetric}
                widthMode="content"
                onChange={(value) => {
                  if (value === "value" || value === "quantity") {
                    onBillingMetricChange(value);
                  }
                }}
                options={[
                  {
                    value: "value",
                    label: BILLING_METRIC_CONTENT.value.shortLabel,
                  },
                  {
                    value: "quantity",
                    label: BILLING_METRIC_CONTENT.quantity.shortLabel,
                  },
                ]}
              />
            </div>
          ) : null}
          <CommercialSelectField
            label="Período"
            hint={CM_HELP.customerDetail.purchaseEvolutionPeriod}
            options={PERIOD_OPTIONS}
            value={String(windowMonths)}
            onChange={(value) => onWindowMonthsChange(parseWindowMonths(value))}
            allowEmpty={false}
          />
        </div>
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
        <ChartViewShell
          prefix="cm"
          overlaysLabel={ANALYTICS_CONTENT.overview.chartOverlaysLabel}
          typeToggleLabel={ANALYTICS_CONTENT.overview.chartTypeLabel}
          typeToggle={
            <ChartTypeSegmentToggle
              family="period_compare"
              value={chartType}
              onChange={setChartType}
              idPrefix="purchase-evolution-type"
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
                  payload: buildPurchaseEvolutionExportPayload(chartData),
                });
              }}
            />
          }
          overlays={
            <ChartOverlayOptionsPopover
              idPrefix="purchase-evolution-overlays"
              portalScopeClassName="dashboard-commercial"
              panelTitle={ANALYTICS_CONTENT.overview.chartOverlaysPanelTitle}
              emptySummaryLabel={ANALYTICS_CONTENT.overview.chartOverlaysEmpty}
              options={overlayOptions}
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
            trendSeriesName={CUSTOMER_BILLING_CONTENT.trendLineSeriesName}
            formatY={formatAxis}
            formatTooltipValue={formatTip}
          />
        </ChartViewShell>
      )}
    </ChartCard>
  );
}
