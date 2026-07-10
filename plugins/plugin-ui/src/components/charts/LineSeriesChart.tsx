import { ChartPlotAreaGroup } from "./seriesChart";
import { SeriesChartPrimitive, type SeriesChartPrimitiveProps } from "./SeriesChartPrimitive";

export type LineSeriesChartProps = Omit<SeriesChartPrimitiveProps, "chartType" | "renderPlotArea">;

/** Gráfico de linha — deriva do primitivo de série. */
export function LineSeriesChart(props: LineSeriesChartProps) {
  return (
    <SeriesChartPrimitive
      {...props}
      chartType="line"
      renderPlotArea={(plotProps) => <ChartPlotAreaGroup {...plotProps} />}
    />
  );
}
