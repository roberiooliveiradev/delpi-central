import type { AnnualComparisonData } from "../types/consumptionAnalysis";
import { formatNumberPtBr } from "../utils/formatters";
import {
  EssModernMultiLineChart,
  type EssModernMultiLinePoint,
  type EssModernMultiLineSeries,
} from "./EssModernMultiLineChart";

type ConsumptionAnnualComparisonChartProps = {
  comparison: AnnualComparisonData | null | undefined;
};

export function buildAnnualComparisonChartModel(
  comparison: AnnualComparisonData,
): {
  points: EssModernMultiLinePoint[];
  series: EssModernMultiLineSeries[];
} {
  const series: EssModernMultiLineSeries[] = comparison.years.map((year) => ({
    key: year,
    label: year,
  }));
  const points: EssModernMultiLinePoint[] = comparison.items.map((item) => {
    const point: EssModernMultiLinePoint = { label: item.month_label };
    for (const year of comparison.years) {
      const value = item.values_by_year[year];
      point[year] = typeof value === "number" ? value : null;
    }
    return point;
  });
  return { points, series };
}

function formatChartValue(value: number): string {
  return formatNumberPtBr(value, value >= 100 ? 0 : 2);
}

export function ConsumptionAnnualComparisonChart({
  comparison,
}: ConsumptionAnnualComparisonChartProps) {
  if (!comparison || comparison.years.length === 0) {
    return (
      <p className="ess-detail__empty">Sem série anual para o comparativo.</p>
    );
  }

  const { points, series } = buildAnnualComparisonChartModel(comparison);

  return (
    <EssModernMultiLineChart
      points={points}
      series={series}
      formatValue={formatChartValue}
      emptyMessage="Sem consumo nos últimos 3 anos para montar o comparativo."
      className="ess-analysis-annual-chart"
    />
  );
}
