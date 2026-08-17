import type { MouseEvent as ReactMouseEvent, PointerEvent as ReactPointerEvent } from "react";

import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  chartPartDomProps,
  isChartPartInteractionSelected,
  resolveChartLinePartStroke,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import type { SeriesChartLayout } from "./layout";

export type ChartGoalLineProps = {
  layout: SeriesChartLayout;
  value: number;
  visible?: boolean;
  interaction?: SeriesChartInteraction | null;
  chartParts?: ChartPartsMap | null;
};

/**
 * Linha de meta no eixo de valores (horizontal no cartesian vertical;
 * vertical no `horizontal_bar`).
 */
export function ChartGoalLine({
  layout,
  value,
  visible = true,
  interaction,
  chartParts,
}: ChartGoalLineProps) {
  const cn = useSeriesChartClasses();
  const ref = { kind: "goalLine" as const };
  const selected = isChartPartInteractionSelected(ref, interaction?.selectedPart);
  const interactive = Boolean(interaction?.onPartPointerDown || interaction?.onPartDoubleClick);
  const lineStroke = resolveChartLinePartStroke(chartParts, ref);

  if (!visible || !Number.isFinite(value)) return null;

  const { margin, plotW, plotH, orientation, toY, toValueX } = layout;
  const isHorizontal = orientation === "horizontal";
  const x1 = isHorizontal ? toValueX?.(value) ?? margin.left : margin.left;
  const x2 = isHorizontal ? x1 : margin.left + plotW;
  const y1 = isHorizontal ? margin.top : toY(value);
  const y2 = isHorizontal ? margin.top + plotH : y1;

  const onPointerDown = interactive
    ? (event: ReactPointerEvent) => {
        event.stopPropagation();
        interaction?.onPartPointerDown?.(ref, event);
      }
    : undefined;

  const onDoubleClick = interactive
    ? (event: ReactMouseEvent) => {
        event.stopPropagation();
        event.preventDefault();
        interaction?.onPartDoubleClick?.(ref, event);
      }
    : undefined;

  const strokeAttrs = {
    ...(lineStroke.stroke ? { stroke: lineStroke.stroke } : {}),
    ...(lineStroke.strokeWidth != null ? { strokeWidth: lineStroke.strokeWidth } : {}),
    ...(lineStroke.opacity != null ? { opacity: lineStroke.opacity } : {}),
  };

  return (
    <g
      className={selected ? `${cn.root}__part--selected` : undefined}
      {...chartPartDomProps(ref, interaction?.selectedPart)}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    >
      {interactive ? (
        <line
          x1={x1}
          y1={y1}
          x2={x2}
          y2={y2}
          stroke="transparent"
          strokeWidth={10}
          pointerEvents="stroke"
        />
      ) : null}
      <line
        x1={x1}
        y1={y1}
        x2={x2}
        y2={y2}
        className={cn.goalLine}
        pointerEvents="none"
        {...strokeAttrs}
      />
    </g>
  );
}
