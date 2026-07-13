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

export type ChartGridProps = {
  layout: SeriesChartLayout;
  showHorizontal?: boolean;
  showVertical?: boolean;
  pointCount: number;
  interaction?: SeriesChartInteraction | null;
  chartParts?: ChartPartsMap | null;
};

export function ChartGrid({
  layout,
  showHorizontal = true,
  showVertical = false,
  pointCount,
  interaction,
  chartParts,
}: ChartGridProps) {
  const cn = useSeriesChartClasses();
  const { margin, plotW, plotH, ticks, toX, toY } = layout;
  const ref = { kind: "grid" as const };
  const selected = isChartPartInteractionSelected(ref, interaction?.selectedPart);
  const interactive = Boolean(interaction?.onPartPointerDown || interaction?.onPartDoubleClick);
  const lineStroke = resolveChartLinePartStroke(chartParts, ref);

  if (!showHorizontal && !showVertical) return null;

  const onGridPointerDown = interactive
    ? (event: ReactPointerEvent) => {
        event.stopPropagation();
        interaction?.onPartPointerDown?.(ref, event);
      }
    : undefined;

  const onGridDoubleClick = interactive
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
      onPointerDown={onGridPointerDown}
      onDoubleClick={onGridDoubleClick}
    >
      {showHorizontal
        ? ticks.map((tick, tickIndex) => {
            // Não desenha grade nos extremos — coincide com o topo/base do plot e “vaza” como moldura.
            if (tickIndex === 0 || tickIndex === ticks.length - 1) return null;
            const y = toY(tick);
            return (
              <g key={`grid-h-${tick}`}>
                {interactive ? (
                  <line
                    x1={margin.left}
                    y1={y}
                    x2={margin.left + plotW}
                    y2={y}
                    stroke="transparent"
                    strokeWidth={8}
                    pointerEvents="stroke"
                  />
                ) : null}
                <line
                  x1={margin.left}
                  y1={y}
                  x2={margin.left + plotW}
                  y2={y}
                  className={cn.gridLine}
                  pointerEvents="none"
                  {...strokeAttrs}
                />
              </g>
            );
          })
        : null}
      {showVertical
        ? Array.from({ length: pointCount }, (_, index) => {
            // Extremos verticais colam na borda do plot — evita moldura fantasma.
            if (index === 0 || index === pointCount - 1) return null;
            const x = toX(index, pointCount);
            return (
              <g key={`grid-v-${index}`}>
                {interactive ? (
                  <line
                    x1={x}
                    y1={margin.top}
                    x2={x}
                    y2={margin.top + plotH}
                    stroke="transparent"
                    strokeWidth={8}
                    pointerEvents="stroke"
                  />
                ) : null}
                <line
                  x1={x}
                  y1={margin.top}
                  x2={x}
                  y2={margin.top + plotH}
                  className={`${cn.gridLine} ${cn.gridLineVertical}`}
                  pointerEvents="none"
                  {...strokeAttrs}
                />
              </g>
            );
          })
        : null}
    </g>
  );
}
