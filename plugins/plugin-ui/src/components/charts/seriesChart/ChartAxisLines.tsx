import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  chartPartDomProps,
  isChartPartRefEqual,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import type { SeriesChartLayout } from "./layout";

export type ChartAxisLinesProps = {
  layout: SeriesChartLayout;
  visible?: boolean;
  interaction?: SeriesChartInteraction | null;
};

export function ChartAxisLines({ layout, visible = true, interaction }: ChartAxisLinesProps) {
  const cn = useSeriesChartClasses();
  if (!visible) return null;

  const { margin, plotW, plotH } = layout;
  const xAxisY = margin.top + plotH;
  const interactive = Boolean(interaction?.onPartPointerDown);
  const xRef = { kind: "axis" as const, axis: "x" as const };
  const yRef = { kind: "axis" as const, axis: "y" as const };
  const xSelected = isChartPartRefEqual(xRef, interaction?.selectedPart);
  const ySelected = isChartPartRefEqual(yRef, interaction?.selectedPart);

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
        />
      </g>
    </>
  );
}
