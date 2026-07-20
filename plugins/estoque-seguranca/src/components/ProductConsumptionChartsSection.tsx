import { useEffect, useState } from "react";

import type {
  AnnualComparisonData,
  MonthlyConsumptionPoint,
} from "../types/consumptionAnalysis";
import { ConsumptionAnnualComparisonChart } from "./ConsumptionAnnualComparisonChart";
import { ConsumptionMonthlyAverageChart } from "./ConsumptionMonthlyAverageChart";

type ChartView = "monthly" | "annual";

const CHART_VIEW_OPTIONS: { value: ChartView; label: string }[] = [
  { value: "monthly", label: "Últimos 12 meses" },
  { value: "annual", label: "Comparativo Anual" },
];

type ProductConsumptionChartsSectionProps = {
  monthlyPoints: MonthlyConsumptionPoint[];
  periodConsumption: number;
  annualComparison?: AnnualComparisonData | null;
  loading?: boolean;
  resetKey?: string | null;
};

export function ProductConsumptionChartsSection({
  monthlyPoints,
  periodConsumption,
  annualComparison,
  loading = false,
  resetKey = null,
}: ProductConsumptionChartsSectionProps) {
  const [chartView, setChartView] = useState<ChartView>("monthly");

  useEffect(() => {
    setChartView("monthly");
  }, [resetKey]);

  return (
    <section className="ess-detail__section" aria-label="Consumo mensal">
      <div className="ess-detail__section-header">
        <h3>Consumo mensal</h3>
      </div>
      <div
        className="ess-chart-tabs"
        role="tablist"
        aria-label="Visão do gráfico de consumo"
      >
        {CHART_VIEW_OPTIONS.map((option) => {
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
      ) : (
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
      )}
    </section>
  );
}
