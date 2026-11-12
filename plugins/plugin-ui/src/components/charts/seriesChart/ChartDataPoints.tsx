import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  CHART_MARKER_RADIUS,
  bindChartPartPointer,
  type ChartPartsMap,
  type SeriesChartInteraction,
  resolveMarkerStyle,
} from "../seriesChartParts";
import { isSeriesChartFiniteValue, type SeriesChartMarkerMode } from "../seriesChartOptions";
import type { SeriesChartSharedProps } from "./types";

export type ChartDataPointsProps = Pick<SeriesChartSharedProps, "layout" | "points" | "seriesColor"> & {
  visible?: boolean;
  interaction?: SeriesChartInteraction | null;
  chartParts?: ChartPartsMap | null;
  seriesIndex?: number;
  plotOn?: "primary" | "secondary";
  /** `last` pinta só o ponto mais recente com valor; default pinta todos. */
  mode?: SeriesChartMarkerMode;
};

/** Índice do último ponto com valor numérico — o «hoje» da série. */
function lastValuedIndex(points: ChartDataPointsProps["points"]): number {
  for (let index = points.length - 1; index >= 0; index -= 1) {
    if (isSeriesChartFiniteValue(points[index]?.value)) return index;
  }
  return -1;
}

export function ChartDataPoints({
  layout,
  points,
  seriesColor,
  visible = true,
  interaction,
  chartParts,
  seriesIndex = 0,
  plotOn = "primary",
  mode = "all",
}: ChartDataPointsProps) {
  const cn = useSeriesChartClasses();
  if (!visible) return null;

  const { toX, toY, toYSecondary } = layout;
  const mapY = plotOn === "secondary" && toYSecondary ? toYSecondary : toY;
  const onlyIndex = mode === "last" ? lastValuedIndex(points) : -1;

  return (
    <>
      {points.map((point, index) => {
        if (mode === "last" && index !== onlyIndex) return null;
        if (!isSeriesChartFiniteValue(point.value)) return null;
        const pointIndex =
          typeof point.sourceIndex === "number" && Number.isFinite(point.sourceIndex)
            ? point.sourceIndex
            : index;
        const marker = resolveMarkerStyle(chartParts, seriesIndex, pointIndex, seriesColor);
        if (!marker.visible) return null;
        const ref = { kind: "marker" as const, seriesIndex, pointIndex };
        const { selected, onPointerDown, onDoubleClick, ...dom } = bindChartPartPointer(ref, interaction, {
          moveWhenSelected: false,
        });
        return (
          <circle
            key={`dot-${index}`}
            cx={toX(pointIndex, points.length)}
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
