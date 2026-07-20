import type { MonthlyConsumptionPoint } from "../types/consumptionAnalysis";
import { formatNumberPtBr } from "../utils/formatters";
import { EssModernLineChart } from "./EssModernLineChart";

const MONTHS_IN_ANALYSIS = 12;

type ConsumptionMonthlyAverageChartProps = {
  points: MonthlyConsumptionPoint[];
  periodConsumption: number;
};

export type ConsumptionMonthlyChartPoint = {
  period: string;
  consumption: number;
  monthlyAverage: number;
};

export function buildConsumptionMonthlyChartData(
  points: MonthlyConsumptionPoint[],
  periodConsumption: number,
): ConsumptionMonthlyChartPoint[] {
  const monthlyAverage = Math.max(Number(periodConsumption) || 0, 0) / MONTHS_IN_ANALYSIS;
  return points.map((point) => ({
    period: point.year_month_label,
    consumption: point.consumption_quantity,
    monthlyAverage,
  }));
}

function formatChartValue(value: number): string {
  return formatNumberPtBr(value, value >= 100 ? 0 : 2);
}

export function ConsumptionMonthlyAverageChart({
  points,
  periodConsumption,
}: ConsumptionMonthlyAverageChartProps) {
  const data = buildConsumptionMonthlyChartData(points, periodConsumption);
  const chartPoints = data.map((point) => ({
    label: point.period,
    value: point.consumption,
  }));
  const monthlyAverage = data[0]?.monthlyAverage ?? null;

  return (
    <EssModernLineChart
      points={chartPoints}
      seriesLabel="Consumo mensal"
      formatValue={formatChartValue}
      averageValue={monthlyAverage}
      averageLabel="Média mensal (12 meses)"
      emptyMessage="Sem série mensal para o período."
      className="ess-analysis-monthly-chart"
    />
  );
}
