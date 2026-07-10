import { useSeriesChartClasses } from "../seriesChartClasses";
import type { SeriesChartLegendPosition } from "../seriesChartOptions";

export type ChartLegendProps = {
  seriesName: string;
  seriesColor: string;
  position: SeriesChartLegendPosition;
  visible?: boolean;
};

export function ChartLegend({ seriesName, seriesColor, position, visible = true }: ChartLegendProps) {
  const cn = useSeriesChartClasses();
  if (!visible || position === "hidden") return null;

  const positionClass =
    position === "top" ? cn.legendTop : position === "right" ? cn.legendRight : cn.legendBottom;

  return (
    <ul className={[cn.legend, positionClass].join(" ")} aria-label="Legenda">
      <li className={cn.legendItem}>
        <span className={cn.legendSwatch} style={{ background: seriesColor }} aria-hidden />
        <span>{seriesName}</span>
      </li>
    </ul>
  );
}
