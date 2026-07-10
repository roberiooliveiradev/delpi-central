import { ChartPlotAreaGroup } from "./seriesChart";
import { SeriesChartPrimitive, type SeriesChartPrimitiveProps } from "./SeriesChartPrimitive";

export type BarSeriesChartProps = Omit<SeriesChartPrimitiveProps, "chartType" | "renderPlotArea">;

/** Gráfico de colunas — deriva do primitivo de série. */
export function BarSeriesChart(props: BarSeriesChartProps) {
  return (
    <SeriesChartPrimitive
      {...props}
      chartType="bar"
      renderPlotArea={(plotProps) => <ChartPlotAreaGroup {...plotProps} />}
    />
  );
}
