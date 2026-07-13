import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  chartPartDomProps,
  isChartPartInteractionSelected,
  resolveChartLinePartStroke,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import type { SeriesChartLayout } from "./layout";

export type ChartAxisLinesProps = {
  layout: SeriesChartLayout;
  visible?: boolean;
  interaction?: SeriesChartInteraction | null;
  chartParts?: ChartPartsMap | null;
};

export function ChartAxisLines({
  layout,
  visible = true,
  interaction,
  chartParts,
}: ChartAxisLinesProps) {
  const cn = useSeriesChartClasses();
  if (!visible) return null;

  const { margin, plotW, plotH } = layout;
  const xAxisY = margin.top + plotH;
  const interactive = Boolean(interaction?.onPartPointerDown || interaction?.onPartDoubleClick);
  const xRef = { kind: "axis" as const, axis: "x" as const };
  const yRef = { kind: "axis" as const, axis: "y" as const };
  const xSelected = isChartPartInteractionSelected(xRef, interaction?.selectedPart);
  const ySelected = isChartPartInteractionSelected(yRef, interaction?.selectedPart);
  const xStroke = resolveChartLinePartStroke(chartParts, xRef);
  const yStroke = resolveChartLinePartStroke(chartParts, yRef);

  return (
    <>
      <g
        {...chartPartDomProps(xRef, interaction?.selectedPart)}
        onPointerDown={
          interactive
            ? (event) => {
                event.stopPropagation();
                interaction?.onPartPointerDown?.(xRef, event);
              }
            : undefined
        }
        onDoubleClick={
          interactive
            ? (event) => {
                event.stopPropagation();
                event.preventDefault();
                interaction?.onPartDoubleClick?.(xRef, event);
              }
            : undefined
        }
      >
        {interactive ? (
          <line
            x1={margin.left}
            y1={xAxisY}
            x2={margin.left + plotW}
            y2={xAxisY}
            stroke="transparent"
            strokeWidth={10}
            pointerEvents="stroke"
          />
        ) : null}
        <line
          x1={margin.left}
          y1={xAxisY}
          x2={margin.left + plotW}
          y2={xAxisY}
          className={[cn.axisLine, xSelected ? `${cn.root}__part--selected` : ""]
            .filter(Boolean)
            .join(" ")}
          pointerEvents="none"
          {...(xStroke.stroke ? { stroke: xStroke.stroke } : {})}
          {...(xStroke.strokeWidth != null ? { strokeWidth: xStroke.strokeWidth } : {})}
          {...(xStroke.opacity != null ? { opacity: xStroke.opacity } : {})}
        />
      </g>
      <g
        {...chartPartDomProps(yRef, interaction?.selectedPart)}
        onPointerDown={
          interactive
            ? (event) => {
                event.stopPropagation();
                interaction?.onPartPointerDown?.(yRef, event);
              }
            : undefined
        }
        onDoubleClick={
          interactive
            ? (event) => {
                event.stopPropagation();
                event.preventDefault();
                interaction?.onPartDoubleClick?.(yRef, event);
              }
            : undefined
        }
      >
        {interactive ? (
          <line
            x1={margin.left}
            y1={margin.top}
            x2={margin.left}
            y2={xAxisY}
            stroke="transparent"
            strokeWidth={10}
            pointerEvents="stroke"
          />
        ) : null}
        <line
          x1={margin.left}
          y1={margin.top}
          x2={margin.left}
          y2={xAxisY}
          className={[cn.axisLine, ySelected ? `${cn.root}__part--selected` : ""]
            .filter(Boolean)
            .join(" ")}
          pointerEvents="none"
          {...(yStroke.stroke ? { stroke: yStroke.stroke } : {})}
          {...(yStroke.strokeWidth != null ? { strokeWidth: yStroke.strokeWidth } : {})}
          {...(yStroke.opacity != null ? { opacity: yStroke.opacity } : {})}
        />
      </g>
    </>
  );
}
