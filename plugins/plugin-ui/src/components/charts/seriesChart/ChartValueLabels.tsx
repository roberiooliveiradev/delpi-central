import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  chartPartDomProps,
  chartPartTypographyStyle,
  filterVisibleSeriesPoints,
  isChartPartInteractionSelected,
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
  /** Barras agrupadas: total de séries no slot da categoria. */
  seriesCount?: number;
  interaction?: SeriesChartInteraction | null;
  /** Rosca: raio interno relativo (só `pie`). */
  pieInnerRadiusRatio?: number;
};

function polar(cx: number, cy: number, r: number, angleRad: number) {
  return { x: cx + r * Math.cos(angleRad), y: cy + r * Math.sin(angleRad) };
}

function DataLabelText({
  x,
  y,
  text,
  textAnchor = "middle",
  dominantBaseline,
  seriesIndex,
  pointIndex,
  chartParts,
  interaction,
  interactive,
  className,
  selectedClassName,
}: {
  x: number;
  y: number;
  text: string;
  textAnchor?: "start" | "middle" | "end";
  dominantBaseline?: "auto" | "middle" | "hanging" | "central";
  seriesIndex: number;
  pointIndex: number;
  chartParts?: ChartPartsMap | null;
  interaction?: SeriesChartInteraction | null;
  interactive: boolean;
  className: string;
  selectedClassName: string;
}) {
  const ref = {
    kind: "dataLabel" as const,
    seriesIndex,
    pointIndex,
  };
  const selected = isChartPartInteractionSelected(ref, interaction?.selectedPart);
  const pointStyle = chartPartTypographyStyle(chartParts, ref);

  return (
    <text
      x={x}
      y={y}
      className={[className, selected ? selectedClassName : ""].filter(Boolean).join(" ")}
      textAnchor={textAnchor}
      dominantBaseline={dominantBaseline}
      style={pointStyle}
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
      {text}
    </text>
  );
}

export function ChartValueLabels({
  chartType,
  layout,
  points,
  valueFormat,
  visible = true,
  chartParts,
  seriesIndex = 0,
  seriesCount = 1,
  interaction,
  pieInnerRadiusRatio = 0,
}: ChartValueLabelsProps) {
  const cn = useSeriesChartClasses();
  if (!visible) return null;

  const { margin, plotW, plotH, plotInset, toX, toY, axisMin, axisMax } = layout;
  const visiblePoints = filterVisibleSeriesPoints(points, chartParts, seriesIndex);
  const interactive = Boolean(interaction?.onPartPointerDown || interaction?.onPartDoubleClick);
  const labelShared = {
    seriesIndex,
    chartParts,
    interaction,
    interactive,
    className: cn.dataLabel,
    selectedClassName: `${cn.root}__part--selected`,
  } as const;

  if (chartType === "pie") {
    const values = visiblePoints.map((p) => Math.max(0, Number(p.value) || 0));
    const total = values.reduce((sum, v) => sum + v, 0);
    if (total <= 0) return null;

    const cx = margin.left + plotW / 2;
    const cy = margin.top + plotH / 2;
    const outerR = Math.max(8, Math.min(plotW, plotH) / 2 - 4);
    const innerR = Math.max(0, outerR * Math.min(0.9, Math.max(0, pieInnerRadiusRatio)));
    const labelR = innerR > 0 ? (innerR + outerR) / 2 : outerR * 0.62;

    let angle = -Math.PI / 2;
    return (
      <>
        {visiblePoints.map((point, i) => {
          const value = values[i]!;
          const sweep = (value / total) * Math.PI * 2;
          const mid = angle + sweep / 2;
          angle += sweep;
          if (value <= 0 || sweep < 0.08) return null;
          const pos = polar(cx, cy, labelR, mid);
          return (
            <DataLabelText
              key={`pie-label-${point.sourceIndex}`}
              x={pos.x}
              y={pos.y}
              text={formatChartTick(value, valueFormat)}
              dominantBaseline="middle"
              pointIndex={point.sourceIndex}
              {...labelShared}
            />
          );
        })}
      </>
    );
  }

  if (chartType === "funnel") {
    const values = visiblePoints.map((p) => Math.max(0, Number(p.value) || 0));
    const n = visiblePoints.length;
    if (n === 0) return null;
    const innerH = Math.max(1, plotH - 2 * plotInset);
    const stageH = innerH / n;
    const cx = margin.left + plotW / 2;

    return (
      <>
        {visiblePoints.map((point, i) => {
          const y = margin.top + plotInset + i * stageH + stageH / 2;
          return (
            <DataLabelText
              key={`funnel-label-${point.sourceIndex}`}
              x={cx}
              y={y}
              text={formatChartTick(values[i]!, valueFormat)}
              dominantBaseline="middle"
              pointIndex={point.sourceIndex}
              {...labelShared}
            />
          );
        })}
      </>
    );
  }

  if (chartType === "radar") {
    const values = visiblePoints.map((p) => Math.max(0, Number(p.value) || 0));
    const maxV = Math.max(...values, 1e-6);
    const n = visiblePoints.length;
    if (n < 3) return null;
    const cx = margin.left + plotW / 2;
    const cy = margin.top + plotH / 2;
    const outerR = Math.max(12, Math.min(plotW, plotH) / 2 - 8);

    return (
      <>
        {visiblePoints.map((point, i) => {
          const angle = -Math.PI / 2 + (i / n) * Math.PI * 2;
          const r = outerR * (values[i]! / maxV) + 10;
          const pos = polar(cx, cy, r, angle);
          return (
            <DataLabelText
              key={`radar-label-${point.sourceIndex}`}
              x={pos.x}
              y={pos.y}
              text={formatChartTick(values[i]!, valueFormat)}
              dominantBaseline="middle"
              pointIndex={point.sourceIndex}
              {...labelShared}
            />
          );
        })}
      </>
    );
  }

  if (chartType === "stacked_bar") {
    const values = visiblePoints.map((p) => Math.max(0, Number(p.value) || 0));
    const total = values.reduce((sum, v) => sum + v, 0);
    if (total <= 0) return null;
    const innerH = Math.max(1, plotH - 2 * plotInset);
    const barW = Math.max(12, Math.min(plotW * 0.28, 64));
    const x = margin.left + (plotW - barW) / 2 + barW / 2;
    const baseY = margin.top + plotInset + innerH;
    let fromBottom = 0;

    return (
      <>
        {visiblePoints.map((point, i) => {
          const value = values[i]!;
          const segH = (value / total) * innerH;
          const y = baseY - fromBottom - segH / 2;
          fromBottom += segH;
          if (segH < 8) return null;
          return (
            <DataLabelText
              key={`stack-label-${point.sourceIndex}`}
              x={x}
              y={y}
              text={formatChartTick(value, valueFormat)}
              dominantBaseline="middle"
              pointIndex={point.sourceIndex}
              {...labelShared}
            />
          );
        })}
      </>
    );
  }

  if (chartType === "bar" || chartType === "histogram" || chartType === "waterfall") {
    const count = Math.max(1, seriesCount);
    const safeIndex = Math.min(Math.max(0, seriesIndex), count - 1);

    return (
      <>
        {visiblePoints.map((point) => {
          const raw = Number(point.value);
          const value = Number.isFinite(raw)
            ? Math.min(axisMax, Math.max(axisMin, raw))
            : axisMin;
          const slotW = plotW / Math.max(points.length, 1);
          const groupPad = Math.min(slotW * 0.12, 6);
          const usable = Math.max(slotW - groupPad * 2, 2);
          const innerGap = count > 1 ? Math.min(usable * 0.08, 3) : 0;
          const barW =
            count > 1
              ? Math.max((usable - innerGap * (count - 1)) / count, 2)
              : Math.max(usable * 0.8, 2);
          const clusterOffset = count > 1 ? 0 : (usable - barW) / 2;
          const x =
            margin.left +
            point.sourceIndex * slotW +
            groupPad +
            clusterOffset +
            safeIndex * (barW + innerGap) +
            barW / 2;
          const y = toY(value) - 4;

          return (
            <DataLabelText
              key={`bar-label-${seriesIndex}-${point.sourceIndex}`}
              x={x}
              y={y}
              text={formatChartTick(Number(point.value), valueFormat)}
              pointIndex={point.sourceIndex}
              {...labelShared}
            />
          );
        })}
      </>
    );
  }

  return (
    <>
      {visiblePoints.map((point) => (
        <DataLabelText
          key={`line-label-${seriesIndex}-${point.sourceIndex}`}
          x={toX(point.sourceIndex, points.length)}
          y={toY(Number(point.value)) - 6}
          text={formatChartTick(Number(point.value), valueFormat)}
          pointIndex={point.sourceIndex}
          {...labelShared}
        />
      ))}
    </>
  );
}
