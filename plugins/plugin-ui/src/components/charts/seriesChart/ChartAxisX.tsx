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
  resolveXLabelTextAnchor,
  type SeriesChartLayout,
} from "./layout";
import type { DisplayFormatSpec } from "../../../displayFormat";
import type {
  SeriesChartCategoryLabelFormat,
  SeriesChartPoint,
  SeriesChartValueFormat,
} from "../seriesChartOptions";

export type ChartAxisXProps = {
  layout: SeriesChartLayout;
  points: SeriesChartPoint[];
  showLabels?: boolean;
  showTitle?: boolean;
  title?: string;
  interaction?: SeriesChartInteraction | null;
  chartParts?: ChartPartsMap | null;
  /** Quando horizontal: eixo X mostra ticks de valor. */
  valueFormat?: SeriesChartValueFormat;
  decimalPlaces?: number | null;
  categoryLabelFormat?: SeriesChartCategoryLabelFormat;
  displayValueFormat?: DisplayFormatSpec | null;
  displayCategoryFormat?: DisplayFormatSpec | null;
};

export function ChartAxisX({
  layout,
  points,
  showLabels = true,
  showTitle = false,
  title,
  interaction,
  chartParts,
  valueFormat = "auto",
  decimalPlaces,
  categoryLabelFormat = "raw",
  displayValueFormat,
  displayCategoryFormat,
}: ChartAxisXProps) {
  const cn = useSeriesChartClasses();
  const {
    margin,
    plotH,
    viewH,
    xLabelsRotated,
    categoryLabelRotationDeg,
    toX,
    plotW,
    visibleXLabelIndices,
    orientation,
    ticks,
    toValueX,
  } = layout;
  const xAxisY = margin.top + plotH;
  const axisRef = { kind: "axis" as const, axis: "x" as const };
  const titleRef = { kind: "axisTitle" as const, axis: "x" as const };
  const axisFontSize = resolveChartPartFontSize(
    "axis",
    getChartPartState(chartParts, axisRef)?.style,
  );
  const absRot = Math.abs(categoryLabelRotationDeg);
  const labelY = xLabelsRotated
    ? xAxisY + Math.round(axisFontSize * (absRot >= 90 ? 1.55 : 1.3))
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
  const horizontal = orientation === "horizontal";

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
      {showLabels && horizontal && toValueX
        ? ticks.map((tick, tickIndex) => {
            const x = toValueX(tick);
            const baseline = tickIndex === 0 ? "hanging" : "hanging";
            return (
              <text
                key={`xv-${tick}`}
                x={x}
                y={xAxisY + Math.round(axisFontSize * 1.05)}
                className={`${cn.tick} ${cn.tickX}`}
                textAnchor="middle"
                dominantBaseline={baseline}
                style={axisTypography}
              >
                {formatChartTick(tick, valueFormat, decimalPlaces, displayValueFormat)}
              </text>
            );
          })
        : null}
      {showLabels && !horizontal
        ? points.map((point, index) => {
            if (!visibleSet.has(index)) return null;
            const x = toX(index, points.length);
            const label = resolveCategoryAxisLabelText(
              String(point.label ?? index + 1),
              categoryLabelFormat,
              layout.categoryLabelOverflow,
              displayCategoryFormat,
            );
            const rotatedClass =
              categoryLabelRotationDeg === -90
                ? cn.tickXRotated90
                : categoryLabelRotationDeg === -45
                  ? cn.tickXRotated45
                  : xLabelsRotated
                    ? cn.tickXRotated
                    : "";
            const className = [cn.tick, cn.tickX, rotatedClass].filter(Boolean).join(" ");

            return (
              <text
                key={`x-${index}`}
                x={x}
                y={labelY}
                className={className}
                textAnchor={resolveXLabelTextAnchor(
                  index,
                  points.length,
                  xLabelsRotated,
                  layout.categoryScale,
                )}
                transform={
                  categoryLabelRotationDeg !== 0
                    ? `rotate(${categoryLabelRotationDeg} ${x} ${labelY})`
                    : undefined
                }
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
