import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  bindChartPartPointer,
  filterVisibleSeriesPoints,
  getChartPartState,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import type { SeriesChartSharedProps } from "./types";

export type ChartSeriesBubbleProps = Pick<SeriesChartSharedProps, "layout" | "points" | "seriesColor"> & {
  interaction?: SeriesChartInteraction | null;
  seriesIndex?: number;
  chartParts?: ChartPartsMap | null;
};

const MIN_R = 4;
const MAX_R = 22;

/** Bolhas: dispersão com raio ∝ |valor|. */
export function ChartSeriesBubble({
  layout,
  points,
  seriesColor,
  interaction,
  seriesIndex = 0,
  chartParts,
}: ChartSeriesBubbleProps) {
  const cn = useSeriesChartClasses();
  const { toX, toY } = layout;
  const seriesRef = { kind: "series" as const, seriesIndex };
  const seriesVisible = getChartPartState(chartParts, seriesRef)?.visible !== false;
  if (!seriesVisible) return null;

  const visiblePoints = filterVisibleSeriesPoints(points, chartParts, seriesIndex);
  if (visiblePoints.length === 0) return null;

  const absValues = visiblePoints.map((p) => Math.abs(Number(p.value) || 0));
  const maxAbs = Math.max(...absValues, 1e-6);

  const { selected, onPointerDown, onDoubleClick, ...dom } = bindChartPartPointer(seriesRef, interaction, {
    moveWhenSelected: false,
  });

  return (
    <g
      className={[cn.seriesBubble, selected ? `${cn.root}__part--selected` : ""]
        .filter(Boolean)
        .join(" ")}
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    >
      {visiblePoints.map((point, i) => {
        const abs = absValues[i]!;
        const r = MIN_R + (Math.sqrt(abs / maxAbs) * (MAX_R - MIN_R));
        return (
          <circle
            key={`bubble-${point.sourceIndex}`}
            cx={toX(point.sourceIndex, points.length)}
            cy={toY(Number(point.value))}
            r={r}
            fill={seriesColor}
            fillOpacity={0.55}
            stroke={seriesColor}
            strokeWidth={1.25}
          />
        );
      })}
    </g>
  );
}
