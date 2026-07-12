import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  chartPartDomProps,
  filterVisibleSeriesPoints,
  isChartPartRefEqual,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import { formatChartTick } from "./layout";
import type { SeriesChartKindProps } from "./types";

export type ChartValueLabelsProps = Pick<
  SeriesChartKindProps,
  "chartType" | "layout" | "points" | "valueFormat"
> & {
  visible?: boolean;
  chartParts?: ChartPartsMap | null;
  seriesIndex?: number;
  interaction?: SeriesChartInteraction | null;
};

export function ChartValueLabels({
  chartType,
  layout,
  points,
  valueFormat,
  visible = true,
  chartParts,
  seriesIndex = 0,
  interaction,
}: ChartValueLabelsProps) {
  const cn = useSeriesChartClasses();
  if (!visible) return null;

  const { margin, plotW, toX, toY } = layout;
  const visiblePoints = filterVisibleSeriesPoints(points, chartParts, seriesIndex);
  const interactive = Boolean(interaction?.onPartPointerDown || interaction?.onPartDoubleClick);

  if (chartType === "bar" || chartType === "histogram" || chartType === "waterfall") {
    return (
      <>
        {visiblePoints.map((point) => {
          const value = Number(point.value);
          const barW = plotW / Math.max(points.length, 1);
          const gap = Math.min(barW * 0.2, 8);
          const width = Math.max(barW - gap, 2);
          const x = margin.left + point.sourceIndex * barW + gap / 2;
          const y = toY(value);
          const ref = {
            kind: "dataLabel" as const,
            seriesIndex,
            pointIndex: point.sourceIndex,
          };
          const selected = isChartPartRefEqual(ref, interaction?.selectedPart);

          return (
            <text
              key={`bar-label-${point.sourceIndex}`}
              x={x + width / 2}
              y={y - 4}
              className={[cn.dataLabel, selected ? `${cn.root}__part--selected` : ""]
                .filter(Boolean)
                .join(" ")}
              textAnchor="middle"
              {...chartPartDomProps(ref, interaction?.selectedPart)}
              onPointerDown={
                interactive
                  ? (event) => {
                      event.stopPropagation();
                      interaction?.onPartPointerDown?.(ref, event);
                    }
                  : undefined
              }
              onDoubleClick={
                interactive
                  ? (event) => {
                      event.stopPropagation();
                      event.preventDefault();
                      interaction?.onPartDoubleClick?.(ref, event);
                    }
                  : undefined
              }
            >
              {formatChartTick(value, valueFormat)}
            </text>
          );
        })}
      </>
    );
  }

  return (
    <>
      {visiblePoints.map((point) => {
        const ref = {
          kind: "dataLabel" as const,
          seriesIndex,
          pointIndex: point.sourceIndex,
        };
        const selected = isChartPartRefEqual(ref, interaction?.selectedPart);
        return (
          <text
            key={`line-label-${point.sourceIndex}`}
            x={toX(point.sourceIndex, points.length)}
            y={toY(Number(point.value)) - 6}
            className={[cn.dataLabel, selected ? `${cn.root}__part--selected` : ""]
              .filter(Boolean)
              .join(" ")}
            textAnchor="middle"
            {...chartPartDomProps(ref, interaction?.selectedPart)}
            onPointerDown={
              interactive
                ? (event) => {
                    event.stopPropagation();
                    interaction?.onPartPointerDown?.(ref, event);
                  }
                : undefined
            }
            onDoubleClick={
              interactive
                ? (event) => {
                    event.stopPropagation();
                    event.preventDefault();
                    interaction?.onPartDoubleClick?.(ref, event);
                  }
                : undefined
            }
          >
            {formatChartTick(Number(point.value), valueFormat)}
          </text>
        );
      })}
    </>
  );
}
