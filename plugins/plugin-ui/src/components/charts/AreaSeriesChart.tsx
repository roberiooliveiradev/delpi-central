import { ChartPlotAreaGroup } from "./seriesChart";
import { SeriesChartPrimitive, type SeriesChartPrimitiveProps } from "./SeriesChartPrimitive";

export type AreaSeriesChartProps = Omit<SeriesChartPrimitiveProps, "chartType" | "renderPlotArea">;

/**
 * Gráfico de área — deriva do primitivo de série.
 *
 * Leitura de tendência: com `areaFillGradient` + `smoothLines` + `markerMode: "last"`
 * o volume da série aparece sem competir com o valor do KPI que costuma acompanhá-lo.
 */
export function AreaSeriesChart(props: AreaSeriesChartProps) {
  return (
    <SeriesChartPrimitive
      {...props}
      chartType="area"
      renderPlotArea={(plotProps) => <ChartPlotAreaGroup {...plotProps} />}
    />
  );
}
