import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  bindChartPartPointer,
  filterVisibleSeriesPoints,
  getChartPartState,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import type { SeriesChartSharedProps } from "./types";

export type ChartSeriesWaterfallProps = Pick<SeriesChartSharedProps, "layout" | "points" | "seriesColor"> & {
  interaction?: SeriesChartInteraction | null;
  seriesIndex?: number;
  chartParts?: ChartPartsMap | null;
};

const POS_FILL = "#16a34a";
const NEG_FILL = "#dc2626";
const TOTAL_FILL = "#089bdb";

/**
 * Cascata: barras de variação acumulada (verde ↑ / vermelho ↓) + coluna total.
 */
export function ChartSeriesWaterfall({
  layout,
  points,
  seriesColor,
  interaction,
  seriesIndex = 0,
  chartParts,
}: ChartSeriesWaterfallProps) {
  const cn = useSeriesChartClasses();
  const { margin, plotW, plotH, plotInset } = layout;
  const seriesRef = { kind: "series" as const, seriesIndex };
  const seriesVisible = getChartPartState(chartParts, seriesRef)?.visible !== false;
  if (!seriesVisible) return null;

  const visiblePoints = filterVisibleSeriesPoints(points, chartParts, seriesIndex);
  if (visiblePoints.length === 0) return null;

  const deltas = visiblePoints.map((p) => Number(p.value) || 0);
  type Step = { start: number; end: number; delta: number; isTotal?: boolean; key: number };
  const steps: Step[] = [];
  let running = 0;
  for (let i = 0; i < deltas.length; i++) {
    const delta = deltas[i]!;
    const start = running;
    const end = running + delta;
    steps.push({ start, end, delta, key: visiblePoints[i]!.sourceIndex });
    running = end;
  }
  steps.push({ start: 0, end: running, delta: running, isTotal: true, key: -1 });

  const ys = steps.flatMap((s) => [s.start, s.end]);
  const yMin = Math.min(0, ...ys);
  const yMax = Math.max(0, ...ys);
  const yRange = Math.max(yMax - yMin, 1e-6);
  const innerH = Math.max(1, plotH - 2 * plotInset);
  const toLocalY = (v: number) => margin.top + plotInset + (1 - (v - yMin) / yRange) * innerH;

  const slotW = plotW / steps.length;
  const gap = Math.min(slotW * 0.2, 8);

  const { selected, onPointerDown, onDoubleClick, ...dom } = bindChartPartPointer(seriesRef, interaction, {
    moveWhenSelected: false,
  });

  return (
    <g
      className={[cn.seriesWaterfall, selected ? `${cn.root}__part--selected` : ""]
        .filter(Boolean)
        .join(" ")}
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    >
      {steps.map((step, index) => {
        const y1 = toLocalY(step.start);
        const y2 = toLocalY(step.end);
        const top = Math.min(y1, y2);
        const height = Math.max(Math.abs(y2 - y1), 1);
        const width = Math.max(slotW - gap, 2);
        const x = margin.left + index * slotW + gap / 2;
        const fill = step.isTotal
          ? seriesColor || TOTAL_FILL
          : step.delta >= 0
            ? POS_FILL
            : NEG_FILL;
        return (
          <rect
            key={`wf-${step.key}-${index}`}
            x={x}
            y={top}
            width={width}
            height={height}
            fill={fill}
            rx={1}
          />
        );
      })}
    </g>
  );
}
