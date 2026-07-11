import type { CSSProperties } from "react";

import { useSeriesChartClasses } from "../seriesChartClasses";
import type { SeriesChartLegendPosition } from "../seriesChartOptions";
import {
  bindChartPartPointer,
  getChartPartState,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";

export type ChartLegendProps = {
  seriesName: string;
  seriesColor: string;
  position: SeriesChartLegendPosition;
  visible?: boolean;
  interaction?: SeriesChartInteraction | null;
  chartParts?: ChartPartsMap | null;
};

function partFrameStyle(
  frame: { x: number; y: number; w?: number; h?: number } | undefined,
): CSSProperties | undefined {
  if (!frame) return undefined;
  return {
    position: "absolute",
    left: `${frame.x}%`,
    top: `${frame.y}%`,
    width: frame.w != null ? `${frame.w}%` : "auto",
    height: frame.h != null ? `${frame.h}%` : "auto",
    zIndex: 3,
    margin: 0,
  };
}

export function ChartLegend({
  seriesName,
  seriesColor,
  position,
  visible = true,
  interaction,
  chartParts,
}: ChartLegendProps) {
  const cn = useSeriesChartClasses();
  if (!visible || position === "hidden") return null;

  const positionClass =
    position === "top" ? cn.legendTop : position === "right" ? cn.legendRight : cn.legendBottom;

  const ref = { kind: "legend" as const };
  const frame = getChartPartState(chartParts, ref)?.frame;
  const frameStyle = partFrameStyle(frame);
  const { selected, onPointerDown, onDoubleClick, ...dom } = bindChartPartPointer(ref, interaction);

  return (
    <ul
      className={[
        cn.legend,
        frameStyle ? "" : positionClass,
        frameStyle ? `${cn.root}__part--framed` : "",
        selected ? `${cn.root}__part--selected` : "",
      ]
        .filter(Boolean)
        .join(" ")}
      style={frameStyle}
      aria-label="Legenda"
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    >
      <li className={cn.legendItem}>
        <span className={cn.legendSwatch} style={{ background: seriesColor }} aria-hidden />
        <span>{seriesName}</span>
      </li>
    </ul>
  );
}
