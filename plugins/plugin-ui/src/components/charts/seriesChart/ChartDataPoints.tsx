import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  CHART_MARKER_RADIUS,
  chartPartDomProps,
  isChartPartRefEqual,
  type ChartPartsMap,
  type SeriesChartInteraction,
  resolveMarkerStyle,
} from "../seriesChartParts";
import type { SeriesChartSharedProps } from "./types";

export type ChartDataPointsProps = Pick<SeriesChartSharedProps, "layout" | "points" | "seriesColor"> & {
  visible?: boolean;
  interaction?: SeriesChartInteraction | null;
  chartParts?: ChartPartsMap | null;
  seriesIndex?: number;
};

export function ChartDataPoints({
  layout,
  points,
  seriesColor,
  visible = true,
  interaction,
  chartParts,
  seriesIndex = 0,
}: ChartDataPointsProps) {
  const cn = useSeriesChartClasses();
  if (!visible) return null;

  const { toX, toY } = layout;
  const interactive = Boolean(interaction?.onPartPointerDown || interaction?.onPartDoubleClick);

  return (
    <>
      {points.map((point, index) => {
        const marker = resolveMarkerStyle(chartParts, seriesIndex, index, seriesColor);
        if (!marker.visible) return null;
        const ref = { kind: "marker" as const, seriesIndex, pointIndex: index };
        const selected = isChartPartRefEqual(ref, interaction?.selectedPart);
        return (
          <circle
            key={`dot-${index}`}
            cx={toX(index, points.length)}
            cy={toY(Number(point.value))}
            r={marker.radius ?? CHART_MARKER_RADIUS}
            fill={marker.fill}
            stroke={marker.stroke}
            strokeWidth={marker.stroke ? marker.strokeWidth || 1 : undefined}
            className={[cn.seriesMarker, selected ? `${cn.root}__part--selected` : ""]
              .filter(Boolean)
              .join(" ")}
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
          />
        );
      })}
    </>
  );
}
