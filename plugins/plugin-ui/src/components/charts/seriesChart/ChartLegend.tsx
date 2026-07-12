import { useLayoutEffect, useRef, type CSSProperties } from "react";

import { useSeriesChartClasses } from "../seriesChartClasses";
import type { SeriesChartLegendPosition } from "../seriesChartOptions";
import {
  bindChartPartPointer,
  chartPartAllowsResize,
  chartPartTypographyStyle,
  clampChartPartFrame,
  getChartPartState,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import { ChartPartResizeHandles } from "./ChartPartResizeHandles";

export type ChartLegendProps = {
  seriesName: string;
  seriesColor: string;
  position: SeriesChartLegendPosition;
  visible?: boolean;
  interaction?: SeriesChartInteraction | null;
  chartParts?: ChartPartsMap | null;
};

function partFrameStyle(
  frame: { x: number; y: number; w?: number; h?: number } | undefined,
  selected: boolean,
): CSSProperties | undefined {
  if (!frame) {
    return selected ? { position: "relative", zIndex: 3 } : undefined;
  }
  return {
    position: "absolute",
    left: `${frame.x}%`,
    top: `${frame.y}%`,
    width: frame.w != null ? `${frame.w}%` : "auto",
    height: frame.h != null ? `${frame.h}%` : "auto",
    zIndex: 3,
    margin: 0,
    boxSizing: "border-box",
  };
}

export function ChartLegend({
  seriesName,
  seriesColor,
  position,
  visible = true,
  interaction,
  chartParts,
}: ChartLegendProps) {
  const cn = useSeriesChartClasses();
  if (!visible || position === "hidden") return null;

  const positionClass =
    position === "top" ? cn.legendTop : position === "right" ? cn.legendRight : cn.legendBottom;

  const ref = { kind: "legend" as const };
  const frame = getChartPartState(chartParts, ref)?.frame;
  const partStyle = getChartPartState(chartParts, ref)?.style;
  const typographyStyle = chartPartTypographyStyle(chartParts, ref);
  const { selected, onPointerDown, onDoubleClick, ...dom } = bindChartPartPointer(ref, interaction);
  const frameStyle = partFrameStyle(frame, selected);
  const paintStyle: CSSProperties = {
    ...(partStyle?.fill && partStyle.fill !== "transparent" ? { background: partStyle.fill } : {}),
    ...(partStyle?.stroke && partStyle.stroke !== "transparent"
      ? {
          borderColor: partStyle.stroke,
          borderStyle: "solid",
          borderWidth: `${Math.max(0, partStyle.strokeWidth ?? 1)}px`,
        }
      : {}),
    ...(partStyle?.borderRadius != null
      ? { borderRadius: `${Math.max(0, partStyle.borderRadius)}px` }
      : {}),
    ...(partStyle?.opacity != null ? { opacity: partStyle.opacity } : {}),
  };
  const hostStyle =
    frameStyle || typographyStyle || Object.keys(paintStyle).length > 0
      ? { ...frameStyle, ...typographyStyle, ...paintStyle }
      : undefined;
  const showResize = selected && chartPartAllowsResize(ref);
  const hostRef = useRef<HTMLUListElement>(null);

  useLayoutEffect(() => {
    if (!showResize || frame?.w != null || !interaction?.onPartFrameChange || !hostRef.current) return;
    const chartRoot = hostRef.current.closest(".delpi-ui-series-chart, .tdp-series-chart");
    if (!chartRoot) return;
    const rect = chartRoot.getBoundingClientRect();
    const el = hostRef.current.getBoundingClientRect();
    if (rect.width < 1 || rect.height < 1) return;
    interaction.onPartFrameChange(
      ref,
      clampChartPartFrame({
        x: ((el.left - rect.left) / rect.width) * 100,
        y: ((el.top - rect.top) / rect.height) * 100,
        w: Math.max(8, (el.width / rect.width) * 100),
        h: Math.max(4, (el.height / rect.height) * 100),
      }),
    );
  }, [showResize, frame?.w, interaction]);

  return (
    <ul
      ref={hostRef}
      className={[
        cn.legend,
        frameStyle?.position === "absolute" ? "" : positionClass,
        frameStyle?.position === "absolute" ? `${cn.root}__part--framed` : "",
        selected ? `${cn.root}__part--selected` : "",
        showResize ? `${cn.root}__part--resizable` : "",
      ]
        .filter(Boolean)
        .join(" ")}
      style={hostStyle}
      aria-label="Legenda"
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    >
      <li className={cn.legendItem}>
        <span className={cn.legendSwatch} style={{ background: seriesColor }} aria-hidden />
        <span>{seriesName}</span>
      </li>
      <ChartPartResizeHandles
        visible={showResize}
        onResizePointerDown={(handle, event) => {
          interaction?.onPartResizePointerDown?.(ref, event, handle);
        }}
      />
    </ul>
  );
}
