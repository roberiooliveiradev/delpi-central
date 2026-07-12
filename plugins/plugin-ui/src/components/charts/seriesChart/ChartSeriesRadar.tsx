import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  bindChartPartPointer,
  filterVisibleSeriesPoints,
  getChartPartState,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import type { SeriesChartSharedProps } from "./types";

export type ChartSeriesRadarProps = Pick<SeriesChartSharedProps, "layout" | "points" | "seriesColor"> & {
  interaction?: SeriesChartInteraction | null;
  seriesIndex?: number;
  chartParts?: ChartPartsMap | null;
};

function polar(cx: number, cy: number, r: number, angleRad: number) {
  return { x: cx + r * Math.cos(angleRad), y: cy + r * Math.sin(angleRad) };
}

/** Radar: polígono polar a partir dos pontos (sem eixos cartesianos). */
export function ChartSeriesRadar({
  layout,
  points,
  seriesColor,
  interaction,
  seriesIndex = 0,
  chartParts,
}: ChartSeriesRadarProps) {
  const cn = useSeriesChartClasses();
  const { margin, plotW, plotH } = layout;
  const seriesRef = { kind: "series" as const, seriesIndex };
  const seriesVisible = getChartPartState(chartParts, seriesRef)?.visible !== false;
  if (!seriesVisible) return null;

  const visiblePoints = filterVisibleSeriesPoints(points, chartParts, seriesIndex);
  if (visiblePoints.length < 3) return null;

  const values = visiblePoints.map((p) => Math.max(0, Number(p.value) || 0));
  const maxV = Math.max(...values, 1e-6);
  const cx = margin.left + plotW / 2;
  const cy = margin.top + plotH / 2;
  const outerR = Math.max(12, Math.min(plotW, plotH) / 2 - 8);
  const n = visiblePoints.length;

  const { selected, onPointerDown, onDoubleClick, ...dom } = bindChartPartPointer(seriesRef, interaction, {
    moveWhenSelected: false,
  });

  const rings = [0.33, 0.66, 1];
  const verts = values.map((value, i) => {
    const angle = -Math.PI / 2 + (i / n) * Math.PI * 2;
    return polar(cx, cy, outerR * (value / maxV), angle);
  });
  const polygon = verts.map((v) => `${v.x},${v.y}`).join(" ");

  return (
    <g
      className={[cn.seriesRadar, selected ? `${cn.root}__part--selected` : ""]
        .filter(Boolean)
        .join(" ")}
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    >
      {rings.map((ratio) => (
        <circle
          key={`ring-${ratio}`}
          cx={cx}
          cy={cy}
          r={outerR * ratio}
          fill="none"
          stroke="var(--delpi-ui-series-chart-grid, #94a3b8)"
          strokeWidth={0.75}
          opacity={0.55}
        />
      ))}
      {Array.from({ length: n }, (_, i) => {
        const angle = -Math.PI / 2 + (i / n) * Math.PI * 2;
        const tip = polar(cx, cy, outerR, angle);
        return (
          <line
            key={`spoke-${i}`}
            x1={cx}
            y1={cy}
            x2={tip.x}
            y2={tip.y}
            stroke="var(--delpi-ui-series-chart-grid, #94a3b8)"
            strokeWidth={0.75}
            opacity={0.45}
          />
        );
      })}
      <polygon
        points={polygon}
        fill={seriesColor}
        fillOpacity={0.28}
        stroke={seriesColor}
        strokeWidth={2}
        strokeLinejoin="round"
      />
      {verts.map((v, i) => (
        <circle key={`rv-${i}`} cx={v.x} cy={v.y} r={3} fill={seriesColor} stroke="#ffffff" strokeWidth={1} />
      ))}
    </g>
  );
}
