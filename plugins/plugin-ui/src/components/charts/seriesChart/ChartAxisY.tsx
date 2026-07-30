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
import {
  formatChartTick,
  resolveCategoryAxisLabelText,
  resolveYAxisTitleAnchorX,
  type SeriesChartLayout,
} from "./layout";
import type {
  SeriesChartCategoryLabelFormat,
  SeriesChartPoint,
  SeriesChartValueFormat,
} from "../seriesChartOptions";

export type ChartAxisYProps = {
  layout: SeriesChartLayout;
  showLabels?: boolean;
  showTitle?: boolean;
  title?: string;
  valueFormat: SeriesChartValueFormat;
  decimalPlaces?: number | null;
  interaction?: SeriesChartInteraction | null;
  chartParts?: ChartPartsMap | null;
  /** Quando horizontal: categorias no eixo Y. */
  points?: SeriesChartPoint[];
  categoryLabelFormat?: SeriesChartCategoryLabelFormat;
};

export function ChartAxisY({
  layout,
  showLabels = true,
  showTitle = false,
  title,
  valueFormat,
  decimalPlaces,
  interaction,
  chartParts,
  points = [],
  categoryLabelFormat = "raw",
}: ChartAxisYProps) {
  const cn = useSeriesChartClasses();
  const { margin, plotH, ticks, toY, orientation, visibleXLabelIndices } = layout;
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
  const titleX = resolveYAxisTitleAnchorX(margin.left, titleFontSize);
  const titleEditWidth = Math.max(
    titleFontSize + 8,
    Math.min(Math.max(margin.left, 28), Math.round(titleFontSize * 1.35)),
  );
  const horizontal = orientation === "horizontal";
  const visibleSet = new Set(visibleXLabelIndices);

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
          x={titleX}
          y={axisCenterY}
          editWidth={titleEditWidth}
          editHeight={Math.min(plotH, Math.max(120, (title?.length ?? 8) * titleFontSize * 0.7))}
          textAnchor="middle"
          rotate={`rotate(-90 ${titleX} ${axisCenterY})`}
          interaction={interaction}
          chartParts={chartParts}
        />
      ) : null}
      {showLabels && horizontal
        ? points.map((point, index) => {
            if (!visibleSet.has(index)) return null;
            const bandStart = layout.categoryBandStartY?.(index, points.length) ?? margin.top;
            const bandH = layout.categoryBandHeight?.(points.length) ?? plotH;
            const y = bandStart + bandH / 2;
            const label = resolveCategoryAxisLabelText(
              String(point.label ?? index + 1),
              categoryLabelFormat,
              layout.categoryLabelOverflow,
            );
            return (
              <text
                key={`yc-${index}`}
                x={margin.left - 6}
                y={y}
                className={`${cn.tick} ${cn.tickY}`}
                textAnchor="end"
                dominantBaseline="middle"
                style={axisTypography}
              >
                {label}
              </text>
            );
          })
        : null}
      {showLabels && !horizontal
        ? ticks.map((tick, tickIndex) => {
            const y = toY(tick);
            const baseline = tickIndex === ticks.length - 1 ? "hanging" : "middle";
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
                {formatChartTick(tick, valueFormat, decimalPlaces)}
              </text>
            );
          })
        : null}
      {showLabels && !horizontal && layout.hasSecondaryAxis && layout.secondaryTicks && layout.toYSecondary
        ? layout.secondaryTicks.map((tick, tickIndex) => {
            const y = layout.toYSecondary!(tick);
            const baseline =
              tickIndex === layout.secondaryTicks!.length - 1 ? "hanging" : "middle";
            return (
              <text
                key={`y2-${tick}`}
                x={layout.viewW - margin.right + 6}
                y={y}
                className={`${cn.tick} ${cn.tickY}`}
                textAnchor="start"
                dominantBaseline={baseline}
                style={axisTypography}
              >
                {formatChartTick(tick, valueFormat, decimalPlaces)}
              </text>
            );
          })
        : null}
    </g>
  );
}
