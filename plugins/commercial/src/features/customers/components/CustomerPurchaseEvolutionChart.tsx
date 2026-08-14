import { useMemo } from "react";
import {
  ChartCard,
  ChartTypeSegmentToggle,
  ChartViewShell,
  chartCardBemClasses,
  EmptyState,
  MultiTypeSeriesChart,
  NativeCheckboxControl,
  PERIOD_COMPARE_TYPES,
  runTabularExport,
  usePersistedChartPreferences,
} from "@delpi/plugin-ui/index";

import {
  CommercialSelectField,
  CommercialTabularExportButtons,
  cmEmptyStateClassNames,
} from "../../../app/commercialUi";
import { CUSTOMER_BILLING_CONTENT } from "../../../content/customerBillingContent";
import { CM_HELP } from "../../../content/helpTooltips";
import { formatCurrency } from "../../../utils/format";
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

function parseWindowMonths(value: string): PurchaseEvolutionWindowMonths {
  return value === "6" ? 6 : 12;
}

export function CustomerPurchaseEvolutionChart({
  points,
  loading,
  error,
  windowMonths,
  onWindowMonthsChange,
}: CustomerPurchaseEvolutionChartProps) {
  const { preferences, setPreferences, setChartType } = usePersistedChartPreferences({
    storageKey: "commercial:account:purchase-evolution",
    defaults: { chartType: "column", showTrend: false },
    allowedChartTypes: PERIOD_COMPARE_TYPES,
  });
  const showTrend = Boolean(preferences.showTrend);
  const chartType = preferences.chartType ?? "column";
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

  const bars = useMemo(
    () => [
      {
        dataKey: "atual",
        name: `Período atual · ${formatCurrency(totals.atual)}`,
        fill: COLOR_CURRENT,
        trendSource: true,
      },
      {
        dataKey: "anterior",
        name: `Período anterior · ${formatCurrency(totals.anterior)}`,
        fill: COLOR_PRIOR,
      },
    ],
    [totals.atual, totals.anterior],
  );

  const emptyMessage =
    windowMonths === 6
      ? "Sem faturamento registrado nos últimos 12 meses para este cliente."
      : "Sem faturamento registrado nos últimos 24 meses para este cliente.";

  return (
    <ChartCard
      title="Evolução de compras"
      titleHint={CM_HELP.customerDetail.purchaseEvolution}
      hint={CM_HELP.customerDetail.purchaseEvolutionComparison}
      classNames={CHART_CLASSES}
      className="cm-purchase-evolution"
      headerActions={
        <CommercialSelectField
          label="Período"
          hint={CM_HELP.customerDetail.purchaseEvolutionPeriod}
          options={PERIOD_OPTIONS}
          value={String(windowMonths)}
          onChange={(value) => onWindowMonthsChange(parseWindowMonths(value))}
          allowEmpty={false}
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
          defaultMessage={emptyMessage}
        />
      ) : (
        <ChartViewShell
          prefix="cm"
          typeToggle={
            <ChartTypeSegmentToggle
              family="period_compare"
              value={chartType}
              onChange={setChartType}
              idPrefix="purchase-evolution-type"
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
                  payload: buildPurchaseEvolutionExportPayload(chartData),
                });
              }}
            />
          }
          overlays={
            <NativeCheckboxControl
              id="customer-purchase-evolution-trend"
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
            trendSeriesName={CUSTOMER_BILLING_CONTENT.trendLineSeriesName}
            formatY={formatChartCurrency}
            formatTooltipValue={formatCurrency}
          />
        </ChartViewShell>
      )}
    </ChartCard>
  );
}
