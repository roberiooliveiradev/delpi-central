import { useEffect, useMemo, useState } from "react";

import type {
  AnnualComparisonData,
  MonthlyConsumptionPoint,
} from "../types/consumptionAnalysis";
import type {
  SafetyStockCollectionBlock,
  SafetyStockProjectionLedgerEntry,
  SafetyStockProjectionSummary,
} from "../types/safetyStock";
import { ConsumptionAnnualComparisonChart } from "./ConsumptionAnnualComparisonChart";
import { ConsumptionMonthlyAverageChart } from "./ConsumptionMonthlyAverageChart";
import { StockProjectionChart } from "./StockProjectionChart";

type ChartView = "monthly" | "annual" | "projection";

type ChartViewOption = { value: ChartView; label: string };

const BASE_CHART_VIEW_OPTIONS: ChartViewOption[] = [
  { value: "monthly", label: "Últimos 12 meses" },
  { value: "annual", label: "Comparativo Anual" },
];

type ProductConsumptionChartsSectionProps = {
  monthlyPoints: MonthlyConsumptionPoint[];
  periodConsumption: number;
  periodStart?: string | null;
  periodEnd?: string | null;
  annualComparison?: AnnualComparisonData | null;
  stockProjection?: SafetyStockCollectionBlock<
    SafetyStockProjectionLedgerEntry,
    SafetyStockProjectionSummary
  > | null;
  loading?: boolean;
  resetKey?: string | null;
};

export function ProductConsumptionChartsSection({
  monthlyPoints,
  periodConsumption,
  periodStart = null,
  periodEnd = null,
  annualComparison,
  stockProjection = null,
  loading = false,
  resetKey = null,
}: ProductConsumptionChartsSectionProps) {
  const hasProjection = Boolean(stockProjection?.summary);
  const chartViewOptions = useMemo(() => {
    if (!hasProjection) return BASE_CHART_VIEW_OPTIONS;
    return [
      ...BASE_CHART_VIEW_OPTIONS,
      { value: "projection" as const, label: "Projeção" },
    ];
  }, [hasProjection]);

  const [chartView, setChartView] = useState<ChartView>("monthly");

  useEffect(() => {
    setChartView("monthly");
  }, [resetKey]);

  useEffect(() => {
    if (chartView === "projection" && !hasProjection) {
      setChartView("monthly");
    }
  }, [chartView, hasProjection]);

  const projectionSummary = stockProjection?.summary;

  return (
    <section className="ess-detail__section" aria-label="Consumo e projeção">
      <div className="ess-detail__section-header">
        <h3>Consumo e projeção</h3>
      </div>
      <div
        className="ess-chart-tabs"
        role="tablist"
        aria-label="Visão do gráfico de consumo e projeção"
      >
        {chartViewOptions.map((option) => {
          const active = chartView === option.value;
          return (
            <button
              key={option.value}
              type="button"
              role="tab"
              aria-selected={active}
              className={
                active
                  ? "ess-chart-tabs__btn ess-chart-tabs__btn--active"
                  : "ess-chart-tabs__btn"
              }
              onClick={() => setChartView(option.value)}
            >
              {option.label}
            </button>
          );
        })}
      </div>
      {chartView === "monthly" ? (
        <>
          <p className="ess-detail__hint">
            Baixas por mês comparadas à média mensal dos últimos 12 meses. Os valores são
            exibidos em cada ponto.
          </p>
          {!loading && monthlyPoints.length === 0 ? (
            <p className="ess-detail__empty">Sem série mensal para o período.</p>
          ) : null}
          {monthlyPoints.length > 0 ? (
            <ConsumptionMonthlyAverageChart
              points={monthlyPoints}
              periodConsumption={periodConsumption}
            />
          ) : null}
        </>
      ) : null}
      {chartView === "annual" ? (
        <>
          <p className="ess-detail__hint">
            Compara o consumo mês a mês nos últimos 3 anos para identificar picos
            sazonais. Meses futuros do ano corrente ficam sem valor.
          </p>
          {!loading && !annualComparison ? (
            <p className="ess-detail__empty">Sem série anual para o comparativo.</p>
          ) : null}
          {annualComparison ? (
            <ConsumptionAnnualComparisonChart comparison={annualComparison} />
          ) : null}
        </>
      ) : null}
      {chartView === "projection" && projectionSummary ? (
        <StockProjectionChart
          items={stockProjection?.items ?? []}
          summary={projectionSummary}
          periodConsumption={periodConsumption}
          periodStart={periodStart}
          periodEnd={periodEnd}
        />
      ) : null}
    </section>
  );
}
