import type { PointerEvent as ReactPointerEvent } from "react";

import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  chartPartDomProps,
  isChartPartRefEqual,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import type { SeriesChartLayout } from "./layout";

export type ChartGridProps = {
  layout: SeriesChartLayout;
  showHorizontal?: boolean;
  showVertical?: boolean;
  pointCount: number;
  interaction?: SeriesChartInteraction | null;
};

export function ChartGrid({
  layout,
  showHorizontal = true,
  showVertical = false,
  pointCount,
  interaction,
}: ChartGridProps) {
  const cn = useSeriesChartClasses();
  const { margin, plotW, plotH, ticks, toX, toY } = layout;
  const ref = { kind: "grid" as const };
  const selected = isChartPartRefEqual(ref, interaction?.selectedPart);
  const interactive = Boolean(interaction?.onPartPointerDown);

  if (!showHorizontal && !showVertical) return null;

  const onGridPointerDown = interactive
    ? (event: ReactPointerEvent) => {
        event.stopPropagation();
        interaction?.onPartPointerDown?.(ref, event);
      }
    : undefined;

  return (
    <g
      className={selected ? `${cn.root}__part--selected` : undefined}
      {...chartPartDomProps(ref, interaction?.selectedPart)}
      onPointerDown={onGridPointerDown}
    >
      {showHorizontal
        ? ticks.map((tick) => {
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
                />
              </g>
            );
          })
        : null}
      {showVertical
        ? Array.from({ length: pointCount }, (_, index) => {
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
                />
              </g>
            );
          })
        : null}
    </g>
  );
}
