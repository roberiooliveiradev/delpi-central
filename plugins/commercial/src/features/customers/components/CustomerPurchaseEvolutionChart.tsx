import { useMemo, useState } from "react";
import {
  ChartCard,
  chartCardBemClasses,
  EmptyState,
  NativeCheckboxControl,
} from "@delpi/plugin-ui/index";

import { CommercialSelectField, cmEmptyStateClassNames } from "../../../app/commercialUi";
import { GroupedColumnSeriesChart } from "../../../components/GroupedColumnSeriesChart";
import { CUSTOMER_BILLING_CONTENT } from "../../../content/customerBillingContent";
import { CM_HELP } from "../../../content/helpTooltips";
import { formatCurrency } from "../../../utils/format";
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
  const [showTrend, setShowTrend] = useState(false);
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
        <div className="cm-purchase-evolution__header-actions">
          <CommercialSelectField
            label="Período"
            hint={CM_HELP.customerDetail.purchaseEvolutionPeriod}
            options={PERIOD_OPTIONS}
            value={String(windowMonths)}
            onChange={(value) => onWindowMonthsChange(parseWindowMonths(value))}
            allowEmpty={false}
          />
          <div className="cm-field">
            <NativeCheckboxControl
              id="customer-purchase-evolution-trend"
              checked={showTrend}
              onChange={setShowTrend}
              label={CUSTOMER_BILLING_CONTENT.showTrendLine}
              hint={CM_HELP.customerDetail.billingSeriesTrend}
            />
          </div>
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
        <GroupedColumnSeriesChart
          data={chartData}
          categoryKey="periodo"
          bars={bars}
          height={CHART_HEIGHT}
          showTrend={showTrend}
          formatY={formatChartCurrency}
          formatTooltipValue={formatCurrency}
        />
      )}
    </ChartCard>
  );
}
