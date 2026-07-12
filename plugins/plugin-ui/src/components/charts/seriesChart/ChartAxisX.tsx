import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  chartPartDomProps,
  chartPartTypographyStyle,
  isChartPartRefEqual,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
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
  const labelY = xLabelsRotated ? xAxisY + 18 : xAxisY + 14;
  const axisRef = { kind: "axis" as const, axis: "x" as const };
  const titleRef = { kind: "axisTitle" as const, axis: "x" as const };
  const interactive = Boolean(interaction?.onPartPointerDown || interaction?.onPartDoubleClick);
  const axisSelected = isChartPartRefEqual(axisRef, interaction?.selectedPart);
  const titleSelected = isChartPartRefEqual(titleRef, interaction?.selectedPart);
  const visibleSet = new Set(visibleXLabelIndices);
  const axisTypography = chartPartTypographyStyle(chartParts, axisRef);
  const titleTypography = chartPartTypographyStyle(chartParts, titleRef);

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
          height={Math.max(viewH - xAxisY, 18)}
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
      {showTitle && title ? (
        <text
          x={margin.left + layout.plotW / 2}
          y={viewH - 4}
          className={[cn.axisTitle, cn.axisTitleX, titleSelected ? `${cn.root}__part--selected` : ""]
            .filter(Boolean)
            .join(" ")}
          textAnchor="middle"
          style={titleTypography}
          {...chartPartDomProps(titleRef, interaction?.selectedPart)}
          onPointerDown={
            interactive
              ? (event) => {
                  event.stopPropagation();
                  interaction?.onPartPointerDown?.(titleRef, event);
                }
              : undefined
          }
          onDoubleClick={
            interactive
              ? (event) => {
                  event.stopPropagation();
                  event.preventDefault();
                  interaction?.onPartDoubleClick?.(titleRef, event);
                }
              : undefined
          }
        >
          {title}
        </text>
      ) : null}
    </g>
  );
}
