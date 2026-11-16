import { ChartPlotAreaGroup } from "./seriesChart";
import {
  SeriesChartPrimitive,
  type SeriesChartPrimitiveProps,
} from "./SeriesChartPrimitive";
import type { SeriesChartPoint } from "./seriesChartOptions";
import type { SeriesChartPointSelection } from "./seriesChartPointSelection";

export type BarSeriesChartProps = Omit<
  SeriesChartPrimitiveProps,
  "chartType" | "renderPlotArea" | "pointSelection"
> & {
  /** Clique na barra/categoria. Segundo clique na selecionada envia `null`. */
  onPointSelect?: (
    point: SeriesChartPoint | null,
    index: number | null,
  ) => void;
  /** Chave da categoria selecionada (`point.label` por padrão). */
  selectedPointKey?: string | null;
  pointKey?: (point: SeriesChartPoint, index: number) => string;
};

/** Gráfico de colunas — deriva do primitivo de série. */
export function BarSeriesChart({
  onPointSelect,
  selectedPointKey,
  pointKey,
  ...props
}: BarSeriesChartProps) {
  const pointSelection: SeriesChartPointSelection | undefined =
    onPointSelect || selectedPointKey != null
      ? { onPointSelect, selectedPointKey, pointKey }
      : undefined;

  return (
    <SeriesChartPrimitive
      {...props}
      chartType="bar"
      pointSelection={pointSelection}
      renderPlotArea={(plotProps) => <ChartPlotAreaGroup {...plotProps} />}
    />
  );
}
