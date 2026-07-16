import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  chartPartDomProps,
  chartPartTypographyStyle,
  getChartPartState,
  isChartPartInteractionSelected,
  resolveChartPartFontSize,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import { ChartAxisTitle } from "./ChartAxisTitle";
import { formatChartTick, type SeriesChartLayout } from "./layout";
import type { SeriesChartValueFormat } from "../seriesChartOptions";

export type ChartAxisYProps = {
  layout: SeriesChartLayout;
  showLabels?: boolean;
  showTitle?: boolean;
  title?: string;
  valueFormat: SeriesChartValueFormat;
  interaction?: SeriesChartInteraction | null;
  chartParts?: ChartPartsMap | null;
};

export function ChartAxisY({
  layout,
  showLabels = true,
  showTitle = false,
  title,
  valueFormat,
  interaction,
  chartParts,
}: ChartAxisYProps) {
  const cn = useSeriesChartClasses();
  const { margin, plotH, ticks, toY } = layout;
  const axisCenterY = margin.top + plotH / 2;
  const axisRef = { kind: "axis" as const, axis: "y" as const };
  const titleRef = { kind: "axisTitle" as const, axis: "y" as const };
  const interactive = Boolean(interaction?.onPartPointerDown || interaction?.onPartDoubleClick);
  const axisSelected = isChartPartInteractionSelected(axisRef, interaction?.selectedPart);
  const axisTypography = chartPartTypographyStyle(chartParts, axisRef);
  const titleFontSize = resolveChartPartFontSize(
    "axisTitle",
    getChartPartState(chartParts, titleRef)?.style,
  );

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
      onDoubleClick={
        interactive
          ? (event) => {
              event.stopPropagation();
              event.preventDefault();
              interaction?.onPartDoubleClick?.(axisRef, event);
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
      {showTitle ? (
        <ChartAxisTitle
          axis="y"
          title={title}
          visible={showTitle}
          x={10}
          y={axisCenterY}
          editWidth={Math.max(margin.left, 28)}
          editHeight={Math.min(plotH, Math.max(120, (title?.length ?? 8) * titleFontSize * 0.7))}
          textAnchor="middle"
          rotate={`rotate(-90 10 ${axisCenterY})`}
          interaction={interaction}
          chartParts={chartParts}
        />
      ) : null}
      {showLabels
        ? ticks.map((tick, tickIndex) => {
            const y = toY(tick);
            const baseline =
              tickIndex === ticks.length - 1
                ? "hanging"
                : tickIndex === 0
                  ? "auto"
                  : "middle";
            return (
              <text
                key={`y-${tick}`}
                x={margin.left - 6}
                y={y}
                className={`${cn.tick} ${cn.tickY}`}
                textAnchor="end"
                dominantBaseline={baseline}
                style={axisTypography}
              >
                {formatChartTick(tick, valueFormat)}
              </text>
            );
          })
        : null}
    </g>
  );
}
