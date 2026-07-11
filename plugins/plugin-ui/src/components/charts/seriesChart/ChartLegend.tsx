import type { CSSProperties } from "react";

import { useSeriesChartClasses } from "../seriesChartClasses";
import type { SeriesChartLegendPosition } from "../seriesChartOptions";
import {
  chartPartDomProps,
  getChartPartState,
  isChartPartRefEqual,
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
  const selected = isChartPartRefEqual(ref, interaction?.selectedPart);
  const interactive = Boolean(interaction?.onPartPointerDown || interaction?.onPartDoubleClick);
  const frame = getChartPartState(chartParts, ref)?.frame;
  const frameStyle = partFrameStyle(frame);

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
      {...chartPartDomProps(ref, interaction?.selectedPart)}
      onPointerDown={
        interactive
          ? (event) => {
              event.stopPropagation();
              interaction?.onPartPointerDown?.(ref, event);
              // Arraste só com a parte já selecionada (duplo clique → depois arrastar).
              if (selected) {
                interaction?.onPartMovePointerDown?.(ref, event);
              }
            }
          : undefined
      }
      onDoubleClick={
        interactive
          ? (event) => {
              event.stopPropagation();
              event.preventDefault();
              interaction?.onPartDoubleClick?.(ref, event);
            }
          : undefined
      }
    >
      <li className={cn.legendItem}>
        <span className={cn.legendSwatch} style={{ background: seriesColor }} aria-hidden />
        <span>{seriesName}</span>
      </li>
    </ul>
  );
}
