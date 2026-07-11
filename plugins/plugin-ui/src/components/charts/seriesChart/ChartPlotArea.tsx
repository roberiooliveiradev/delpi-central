import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  chartPartDomProps,
  isChartPartRefEqual,
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
  const selected = isChartPartRefEqual(ref, interaction?.selectedPart);
  const interactive = Boolean(interaction?.onPartPointerDown);
  const style = resolvePlotAreaStyle(chartParts);

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
      {...chartPartDomProps(ref, interaction?.selectedPart)}
      onPointerDown={
        interactive
          ? (event) => {
              event.stopPropagation();
              interaction?.onPartPointerDown?.(ref, event);
            }
          : undefined
      }
    />
  );
}
