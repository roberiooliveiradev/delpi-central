import { DECK_CATEGORY_PALETTE } from "../../../theme/deckColorCatalog";
import { resolveSeriesCategoryColor } from "../seriesChartOptions";
import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  bindChartPartPointer,
  filterVisibleSeriesPoints,
  getChartPartState,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import type { SeriesChartSharedProps } from "./types";

export type ChartSeriesPieProps = Pick<SeriesChartSharedProps, "layout" | "points" | "seriesColor"> & {
  interaction?: SeriesChartInteraction | null;
  seriesIndex?: number;
  chartParts?: ChartPartsMap | null;
  /** Rosca (doughnut): raio interno relativo 0–0.9. */
  innerRadiusRatio?: number;
  categoryColors?: string[] | null;
};

function polar(cx: number, cy: number, r: number, angleRad: number) {
  return { x: cx + r * Math.cos(angleRad), y: cy + r * Math.sin(angleRad) };
}

function arcPath(
  cx: number,
  cy: number,
  outerR: number,
  innerR: number,
  start: number,
  end: number,
): string {
  const large = end - start > Math.PI ? 1 : 0;
  const o0 = polar(cx, cy, outerR, start);
  const o1 = polar(cx, cy, outerR, end);
  if (innerR <= 0) {
    return [
      `M ${cx} ${cy}`,
      `L ${o0.x} ${o0.y}`,
      `A ${outerR} ${outerR} 0 ${large} 1 ${o1.x} ${o1.y}`,
      "Z",
    ].join(" ");
  }
  const i0 = polar(cx, cy, innerR, end);
  const i1 = polar(cx, cy, innerR, start);
  return [
    `M ${o0.x} ${o0.y}`,
    `A ${outerR} ${outerR} 0 ${large} 1 ${o1.x} ${o1.y}`,
    `L ${i0.x} ${i0.y}`,
    `A ${innerR} ${innerR} 0 ${large} 0 ${i1.x} ${i1.y}`,
    "Z",
  ].join(" ");
}

/** Pizza / rosca — fatias como `marker:0:i`; série = conjunto (4H.7). */
export function ChartSeriesPie({
  layout,
  points,
  seriesColor,
  interaction,
  seriesIndex = 0,
  chartParts,
  innerRadiusRatio = 0,
  categoryColors,
}: ChartSeriesPieProps) {
  const cn = useSeriesChartClasses();
  const { margin, plotW, plotH } = layout;
  const seriesRef = { kind: "series" as const, seriesIndex };
  const seriesVisible = getChartPartState(chartParts, seriesRef)?.visible !== false;
  if (!seriesVisible) return null;

  const visiblePoints = filterVisibleSeriesPoints(points, chartParts, seriesIndex);
  if (visiblePoints.length === 0) return null;

  const values = visiblePoints.map((p) => Math.max(0, Number(p.value) || 0));
  const total = values.reduce((sum, v) => sum + v, 0);
  if (total <= 0) return null;

  const cx = margin.left + plotW / 2;
  const cy = margin.top + plotH / 2;
  const outerR = Math.max(8, Math.min(plotW, plotH) / 2 - 4);
  const innerR = Math.max(0, outerR * Math.min(0.9, Math.max(0, innerRadiusRatio)));

  const { selected, onPointerDown, onDoubleClick, editing: _editing, ...dom } = bindChartPartPointer(
    seriesRef,
    interaction,
    { moveWhenSelected: false },
  );

  let angle = -Math.PI / 2;
  return (
    <g
      className={[cn.seriesPie, selected ? `${cn.root}__part--selected` : ""].filter(Boolean).join(" ")}
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    >
      {visiblePoints.map((point, i) => {
        const value = values[i]!;
        const sweep = (value / total) * Math.PI * 2;
        const start = angle;
        const end = angle + sweep;
        angle = end;
        const markerRef = {
          kind: "marker" as const,
          seriesIndex,
          pointIndex: point.sourceIndex,
        };
        const fill =
          getChartPartState(chartParts, markerRef)?.style?.fill ??
          resolveSeriesCategoryColor(i, seriesColor, categoryColors, DECK_CATEGORY_PALETTE);
        const { selected, onPointerDown, onDoubleClick, ...dom } = bindChartPartPointer(
          markerRef,
          interaction,
          { moveWhenSelected: false },
        );
        return (
          <path
            key={`slice-${point.sourceIndex}`}
            d={arcPath(cx, cy, outerR, innerR, start, end)}
            fill={fill}
            stroke="#ffffff"
            strokeWidth={1}
            vectorEffect="non-scaling-stroke"
            className={[cn.seriesPieSlice, selected ? `${cn.root}__part--selected` : ""]
              .filter(Boolean)
              .join(" ")}
            {...dom}
            onPointerDown={
              onPointerDown
                ? (event) => {
                    event.stopPropagation();
                    onPointerDown(event);
                  }
                : undefined
            }
            onDoubleClick={
              onDoubleClick
                ? (event) => {
                    event.stopPropagation();
                    onDoubleClick(event);
                  }
                : undefined
            }
          />
        );
      })}
    </g>
  );
}
