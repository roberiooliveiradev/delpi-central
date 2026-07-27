import {
  formatSeriesChartDataLabelText,
  resolveDataLabelPosition,
  resolveSeriesChartDataLabels,
  shouldHideDataLabel,
  type SeriesChartDataLabelsResolved,
} from "../seriesChartDataLabels";
import {
  SERIES_CHART_CATEGORY_PALETTE,
  resolveSeriesCategoryColor,
} from "../seriesChartOptions";
import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  chartPartDomProps,
  chartPartTypographyStyle,
  filterVisibleSeriesPoints,
  isChartPartInteractionSelected,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import type { SeriesChartKindProps } from "./types";

export type ChartValueLabelsProps = Pick<
  SeriesChartKindProps,
  "chartType" | "layout" | "points" | "valueFormat" | "config"
> & {
  visible?: boolean;
  chartParts?: ChartPartsMap | null;
  seriesIndex?: number;
  seriesCount?: number;
  seriesName?: string;
  interaction?: SeriesChartInteraction | null;
  pieInnerRadiusRatio?: number;
  dataLabels?: SeriesChartDataLabelsResolved | null;
};

function polar(cx: number, cy: number, r: number, angleRad: number) {
  return { x: cx + r * Math.cos(angleRad), y: cy + r * Math.sin(angleRad) };
}

function DataLabelText({
  x,
  y,
  text,
  fill,
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
  fill?: string;
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
  const pointStyle = {
    ...chartPartTypographyStyle(chartParts, ref),
    ...(fill ? { fill } : {}),
  };
  const lines = text.split("\n");

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
      {lines.length <= 1
        ? text
        : lines.map((line, i) => (
            <tspan key={`dl-${pointIndex}-${i}`} x={x} dy={i === 0 ? 0 : "1.15em"}>
              {line}
            </tspan>
          ))}
    </text>
  );
}

export function ChartValueLabels({
  chartType,
  layout,
  points,
  valueFormat,
  config,
  visible = true,
  chartParts,
  seriesIndex = 0,
  seriesCount = 1,
  seriesName,
  interaction,
  pieInnerRadiusRatio = 0,
  dataLabels: dataLabelsProp,
}: ChartValueLabelsProps) {
  const cn = useSeriesChartClasses();
  const dataLabels =
    dataLabelsProp ??
    resolveSeriesChartDataLabels({
      showDataLabels: visible,
      dataLabels: config.dataLabels,
    });
  if (!visible || !dataLabels) return null;

  const { margin, plotW, plotH, plotInset, toX, toY, axisMin, axisMax } = layout;
  const visiblePoints = filterVisibleSeriesPoints(points, chartParts, seriesIndex);
  const interactive = Boolean(interaction?.onPartPointerDown || interaction?.onPartDoubleClick);
  const position = resolveDataLabelPosition(chartType, dataLabels.position);
  const total = visiblePoints.reduce((sum, p) => sum + Math.max(0, Number(p.value) || 0), 0);
  const resolvedSeriesName = seriesName?.trim() || config.seriesName?.trim() || "";
  const labelShared = {
    seriesIndex,
    chartParts,
    interaction,
    interactive,
    className: cn.dataLabel,
    selectedClassName: `${cn.root}__part--selected`,
  } as const;

  const labelText = (point: (typeof visiblePoints)[number], value: number) =>
    formatSeriesChartDataLabelText({
      config: dataLabels,
      categoryLabel: point.label,
      seriesName: resolvedSeriesName,
      value,
      total,
      valueFormat,
    });

  const categoryFill = (index: number) =>
    dataLabels.colorFromCategory
      ? resolveSeriesCategoryColor(
          index,
          config.seriesColor,
          config.categoryColors,
          SERIES_CHART_CATEGORY_PALETTE,
        )
      : undefined;

  if (chartType === "pie") {
    const values = visiblePoints.map((p) => Math.max(0, Number(p.value) || 0));
    if (total <= 0) return null;

    const cx = margin.left + plotW / 2;
    const cy = margin.top + plotH / 2;
    const outerR = Math.max(8, Math.min(plotW, plotH) / 2 - 4);
    const innerR = Math.max(0, outerR * Math.min(0.9, Math.max(0, pieInnerRadiusRatio)));
    const midR = innerR > 0 ? (innerR + outerR) / 2 : outerR * 0.62;
    const insideEndR = innerR > 0 ? innerR + (outerR - innerR) * 0.78 : outerR * 0.78;
    const outsideR = outerR + Math.min(36, Math.max(16, Math.min(plotW, plotH) * 0.08));

    let angle = -Math.PI / 2;
    return (
      <>
        {visiblePoints.map((point, i) => {
          const value = values[i]!;
          const sweep = (value / total) * Math.PI * 2;
          const mid = angle + sweep / 2;
          angle += sweep;
          if (
            shouldHideDataLabel({ config: dataLabels, value, total }) ||
            (value <= 0 && sweep < 0.02)
          ) {
            return null;
          }
          const text = labelText(point, value);
          if (!text) return null;

          let labelR = midR;
          if (position === "insideEnd") labelR = insideEndR;
          if (position === "outsideEnd") labelR = outsideR;

          const pos = polar(cx, cy, labelR, mid);
          const edge = polar(cx, cy, outerR, mid);
          const fill = categoryFill(i);
          const anchor =
            position === "outsideEnd"
              ? Math.cos(mid) > 0.15
                ? "start"
                : Math.cos(mid) < -0.15
                  ? "end"
                  : "middle"
              : "middle";

          return (
            <g key={`pie-label-${point.sourceIndex}`}>
              {position === "outsideEnd" && dataLabels.showLeaderLines ? (
                <line
                  x1={edge.x}
                  y1={edge.y}
                  x2={pos.x}
                  y2={pos.y}
                  className={cn.dataLabelLeader}
                  stroke={fill || "currentColor"}
                  strokeWidth={1}
                />
              ) : null}
              <DataLabelText
                x={pos.x}
                y={pos.y}
                text={text}
                fill={fill}
                textAnchor={anchor}
                dominantBaseline="middle"
                pointIndex={point.sourceIndex}
                {...labelShared}
              />
            </g>
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
    const maxV = Math.max(...values, 1e-6);
    const innerW = Math.max(1, plotW - 2 * plotInset);

    return (
      <>
        {visiblePoints.map((point, i) => {
          const value = values[i]!;
          if (shouldHideDataLabel({ config: dataLabels, value, total })) return null;
          const text = labelText(point, value);
          if (!text) return null;
          const y = margin.top + plotInset + i * stageH + stageH / 2;
          const stageW = (value / maxV) * innerW;
          let x = cx;
          if (position === "outsideEnd") x = cx + stageW / 2 + 10;
          if (position === "insideEnd") x = cx + Math.max(0, stageW / 2 - 12);
          const fill = categoryFill(i);
          return (
            <g key={`funnel-label-${point.sourceIndex}`}>
              {position === "outsideEnd" && dataLabels.showLeaderLines ? (
                <line
                  x1={cx + stageW / 2}
                  y1={y}
                  x2={x - 2}
                  y2={y}
                  className={cn.dataLabelLeader}
                  stroke={fill || "currentColor"}
                  strokeWidth={1}
                />
              ) : null}
              <DataLabelText
                x={x}
                y={y}
                text={text}
                fill={fill}
                textAnchor={position === "outsideEnd" ? "start" : "middle"}
                dominantBaseline="middle"
                pointIndex={point.sourceIndex}
                {...labelShared}
              />
            </g>
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
          const value = values[i]!;
          if (shouldHideDataLabel({ config: dataLabels, value, total })) return null;
          const text = labelText(point, value);
          if (!text) return null;
          const angle = -Math.PI / 2 + (i / n) * Math.PI * 2;
          const valueR = outerR * (value / maxV);
          const labelR =
            position === "outsideEnd" ? valueR + 14 : position === "insideEnd" ? valueR * 0.85 : valueR + 8;
          const pos = polar(cx, cy, labelR, angle);
          return (
            <DataLabelText
              key={`radar-label-${point.sourceIndex}`}
              x={pos.x}
              y={pos.y}
              text={text}
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
          const yCenter = baseY - fromBottom - segH / 2;
          fromBottom += segH;
          if (shouldHideDataLabel({ config: dataLabels, value, total }) || segH < 6) return null;
          const text = labelText(point, value);
          if (!text) return null;
          const fill = categoryFill(i);
          return (
            <DataLabelText
              key={`stack-label-${point.sourceIndex}`}
              x={x}
              y={yCenter}
              text={text}
              fill={fill}
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
    const baseline = margin.top + plotH;

    return (
      <>
        {visiblePoints.map((point) => {
          const raw = Number(point.value);
          const value = Number.isFinite(raw) ? raw : 0;
          if (shouldHideDataLabel({ config: dataLabels, value, total })) return null;
          const text = labelText(point, value);
          if (!text) return null;
          const clamped = Number.isFinite(raw)
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
          const yTop = toY(clamped);
          let y = yTop - 6;
          if (position === "center") y = (yTop + baseline) / 2;
          if (position === "insideEnd") y = yTop + 12;
          return (
            <DataLabelText
              key={`bar-label-${seriesIndex}-${point.sourceIndex}`}
              x={x}
              y={y}
              text={text}
              dominantBaseline={position === "center" || position === "insideEnd" ? "middle" : undefined}
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
      {visiblePoints.map((point) => {
        const value = Number(point.value);
        if (!Number.isFinite(value)) return null;
        if (shouldHideDataLabel({ config: dataLabels, value, total })) return null;
        const text = labelText(point, value);
        if (!text) return null;
        const yPoint = toY(value);
        let y = yPoint - 8;
        if (position === "center") y = yPoint;
        if (position === "insideEnd") y = yPoint + 10;
        return (
          <DataLabelText
            key={`line-label-${seriesIndex}-${point.sourceIndex}`}
            x={toX(point.sourceIndex, points.length)}
            y={y}
            text={text}
            dominantBaseline={position === "center" ? "middle" : undefined}
            pointIndex={point.sourceIndex}
            {...labelShared}
          />
        );
      })}
    </>
  );
}
