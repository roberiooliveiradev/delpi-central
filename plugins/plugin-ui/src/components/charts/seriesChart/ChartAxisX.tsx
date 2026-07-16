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
import { resolveXLabelTextAnchor, type SeriesChartLayout } from "./layout";
import type { SeriesChartPoint } from "../seriesChartOptions";

export type ChartAxisXProps = {
  layout: SeriesChartLayout;
  points: SeriesChartPoint[];
  showLabels?: boolean;
  showTitle?: boolean;
  title?: string;
  interaction?: SeriesChartInteraction | null;
  chartParts?: ChartPartsMap | null;
};

export function ChartAxisX({
  layout,
  points,
  showLabels = true,
  showTitle = false,
  title,
  interaction,
  chartParts,
}: ChartAxisXProps) {
  const cn = useSeriesChartClasses();
  const { margin, plotH, viewH, xLabelsRotated, toX, plotW, visibleXLabelIndices } = layout;
  const xAxisY = margin.top + plotH;
  const axisRef = { kind: "axis" as const, axis: "x" as const };
  const titleRef = { kind: "axisTitle" as const, axis: "x" as const };
  const axisFontSize = resolveChartPartFontSize(
    "axis",
    getChartPartState(chartParts, axisRef)?.style,
  );
  const labelY = xLabelsRotated
    ? xAxisY + Math.round(axisFontSize * 1.3)
    : xAxisY + Math.round(axisFontSize * 1.05);
  const hitH = Math.max(viewH - xAxisY, Math.round(axisFontSize * 1.6));
  const interactive = Boolean(interaction?.onPartPointerDown || interaction?.onPartDoubleClick);
  const axisSelected = isChartPartInteractionSelected(axisRef, interaction?.selectedPart);
  const visibleSet = new Set(visibleXLabelIndices);
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
          x={margin.left}
          y={xAxisY}
          width={plotW}
          height={hitH}
          fill="transparent"
          pointerEvents="all"
        />
      ) : null}
      {showLabels
        ? points.map((point, index) => {
            if (!visibleSet.has(index)) return null;
            const x = toX(index, points.length);
            const label = String(point.label ?? index + 1);
            const className = [cn.tick, cn.tickX, xLabelsRotated ? cn.tickXRotated : ""]
              .filter(Boolean)
              .join(" ");

            return (
              <text
                key={`x-${index}`}
                x={x}
                y={labelY}
                className={className}
                textAnchor={resolveXLabelTextAnchor(index, points.length, xLabelsRotated)}
                transform={xLabelsRotated ? `rotate(-38 ${x} ${labelY})` : undefined}
                style={axisTypography}
              >
                {label}
              </text>
            );
          })
        : null}
      {showTitle ? (
        <ChartAxisTitle
          axis="x"
          title={title}
          visible={showTitle}
          x={margin.left + layout.plotW / 2}
          y={viewH - 4}
          editWidth={Math.min(plotW, Math.max(80, (title?.length ?? 8) * titleFontSize * 0.65))}
          editHeight={Math.max(22, titleFontSize + 10)}
          textAnchor="middle"
          interaction={interaction}
          chartParts={chartParts}
        />
      ) : null}
    </g>
  );
}
