import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  CHART_MARKER_RADIUS,
  bindChartPartPointer,
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
  plotOn?: "primary" | "secondary";
};

export function ChartDataPoints({
  layout,
  points,
  seriesColor,
  visible = true,
  interaction,
  chartParts,
  seriesIndex = 0,
  plotOn = "primary",
}: ChartDataPointsProps) {
  const cn = useSeriesChartClasses();
  if (!visible) return null;

  const { toX, toY, toYSecondary } = layout;
  const mapY = plotOn === "secondary" && toYSecondary ? toYSecondary : toY;

  return (
    <>
      {points.map((point, index) => {
        const marker = resolveMarkerStyle(chartParts, seriesIndex, index, seriesColor);
        if (!marker.visible) return null;
        const ref = { kind: "marker" as const, seriesIndex, pointIndex: index };
        const { selected, onPointerDown, onDoubleClick, ...dom } = bindChartPartPointer(ref, interaction, {
          moveWhenSelected: false,
        });
        return (
          <circle
            key={`dot-${index}`}
            cx={toX(index, points.length)}
            cy={mapY(Number(point.value))}
            r={marker.radius ?? CHART_MARKER_RADIUS}
            fill={marker.fill}
            stroke={marker.stroke}
            strokeWidth={marker.stroke ? marker.strokeWidth || 1 : undefined}
            className={[cn.seriesMarker, selected ? `${cn.root}__part--selected` : ""]
              .filter(Boolean)
              .join(" ")}
            {...dom}
            onPointerDown={onPointerDown}
            onDoubleClick={onDoubleClick}
          />
        );
      })}
    </>
  );
}
