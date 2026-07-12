import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  bindChartPartPointer,
  resolvePlotAreaStyle,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import type { SeriesChartLayout } from "./layout";

export type ChartPlotAreaProps = {
  layout: SeriesChartLayout;
  showAxes?: boolean;
  interaction?: SeriesChartInteraction | null;
  chartParts?: ChartPartsMap | null;
};

export function ChartPlotArea({
  layout,
  showAxes = true,
  interaction,
  chartParts,
}: ChartPlotAreaProps) {
  const cn = useSeriesChartClasses();
  const { margin, plotW, plotH } = layout;
  const ref = { kind: "plotArea" as const };
  const style = resolvePlotAreaStyle(chartParts);
  const { selected, onPointerDown, onDoubleClick, ...dom } = bindChartPartPointer(ref, interaction);

  return (
    <rect
      x={margin.left}
      y={margin.top}
      width={plotW}
      height={plotH}
      fill={style.fill}
      stroke={style.stroke}
      strokeWidth={style.strokeWidth}
      vectorEffect="non-scaling-stroke"
      className={[cn.plotArea, showAxes ? cn.plotAreaAxes : "", selected ? `${cn.root}__part--selected` : ""]
        .filter(Boolean)
        .join(" ")}
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    />
  );
}
