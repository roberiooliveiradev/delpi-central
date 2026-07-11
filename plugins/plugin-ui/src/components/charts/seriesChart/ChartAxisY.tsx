import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  chartPartDomProps,
  isChartPartRefEqual,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import { formatChartTick, type SeriesChartLayout } from "./layout";
import type { SeriesChartValueFormat } from "../seriesChartOptions";

export type ChartAxisYProps = {
  layout: SeriesChartLayout;
  showLabels?: boolean;
  showTitle?: boolean;
  title?: string;
  valueFormat: SeriesChartValueFormat;
  interaction?: SeriesChartInteraction | null;
};

export function ChartAxisY({
  layout,
  showLabels = true,
  showTitle = false,
  title,
  valueFormat,
  interaction,
}: ChartAxisYProps) {
  const cn = useSeriesChartClasses();
  const { margin, plotH, ticks, toY } = layout;
  const axisCenterY = margin.top + plotH / 2;
  const axisRef = { kind: "axis" as const, axis: "y" as const };
  const titleRef = { kind: "axisTitle" as const, axis: "y" as const };
  const interactive = Boolean(interaction?.onPartPointerDown);
  const axisSelected = isChartPartRefEqual(axisRef, interaction?.selectedPart);
  const titleSelected = isChartPartRefEqual(titleRef, interaction?.selectedPart);

  return (
    <g
      className={axisSelected ? `${cn.root}__part--selected` : undefined}
      {...chartPartDomProps(axisRef, interaction?.selectedPart)}
      onPointerDown={
        interactive
          ? (event) => {
              event.stopPropagation();
              interaction?.onPartPointerDown?.(axisRef, event);
            }
          : undefined
      }
    >
      {interactive ? (
        <rect
          x={0}
          y={margin.top}
          width={Math.max(margin.left, 28)}
          height={plotH}
          fill="transparent"
          pointerEvents="all"
        />
      ) : null}
      {showTitle && title ? (
        <text
          x={10}
          y={axisCenterY}
          className={[cn.axisTitle, cn.axisTitleY, titleSelected ? `${cn.root}__part--selected` : ""]
            .filter(Boolean)
            .join(" ")}
          transform={`rotate(-90 10 ${axisCenterY})`}
          {...chartPartDomProps(titleRef, interaction?.selectedPart)}
          onPointerDown={
            interactive
              ? (event) => {
                  event.stopPropagation();
                  interaction?.onPartPointerDown?.(titleRef, event);
                }
              : undefined
          }
        >
          {title}
        </text>
      ) : null}
      {showLabels
        ? ticks.map((tick) => {
            const y = toY(tick);
            return (
              <text
                key={`y-${tick}`}
                x={margin.left - 6}
                y={y}
                className={`${cn.tick} ${cn.tickY}`}
                textAnchor="end"
                dominantBaseline="middle"
              >
                {formatChartTick(tick, valueFormat)}
              </text>
            );
          })
        : null}
    </g>
  );
}
