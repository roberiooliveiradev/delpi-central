import { type CSSProperties } from "react";

import { useSeriesChartClasses } from "../seriesChartClasses";
import type { SeriesChartLegendPosition } from "../seriesChartOptions";
import {
  bindChartPartPointer,
  chartPartAllowsResize,
  chartPartTypographyStyle,
  getChartPartState,
  looksLikeAutoMaterializedFlowFrame,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import { ChartPartResizeHandles } from "./ChartPartResizeHandles";

export type ChartLegendProps = {
  seriesName: string;
  seriesColor: string;
  /** Quando informado, renderiza uma entrada por série. */
  items?: Array<{ name: string; color: string }>;
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
  items,
  position,
  visible = true,
  interaction,
  chartParts,
}: ChartLegendProps) {
  const cn = useSeriesChartClasses();
  if (!visible || position === "hidden") return null;

  const positionClass =
    position === "top"
      ? cn.legendTop
      : position === "right"
        ? cn.legendRight
        : position === "left"
          ? cn.legendLeft
          : cn.legendBottom;

  const ref = { kind: "legend" as const };
  const rawFrame = getChartPartState(chartParts, ref)?.frame;
  const frame =
    rawFrame && looksLikeAutoMaterializedFlowFrame("legend", rawFrame) ? undefined : rawFrame;
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
  const legendEntries =
    items && items.length > 0 ? items : [{ name: seriesName, color: seriesColor }];

  return (
    <ul
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
      {legendEntries.map((entry, seriesIndex) => {
        const seriesRef = { kind: "series" as const, seriesIndex };
        const {
          selected: seriesSelected,
          editing: _seriesEditing,
          onPointerDown: onSeriesPointerDown,
          onDoubleClick: onSeriesDoubleClick,
          ...seriesDom
        } = bindChartPartPointer(seriesRef, interaction);
        return (
          <li
            key={`${entry.name}-${entry.color}-${seriesIndex}`}
            className={[
              cn.legendItem,
              seriesSelected ? `${cn.root}__part--selected` : "",
            ]
              .filter(Boolean)
              .join(" ")}
            {...seriesDom}
            onPointerDown={
              onSeriesPointerDown
                ? (event) => {
                    event.stopPropagation();
                    onSeriesPointerDown(event);
                  }
                : undefined
            }
            onDoubleClick={
              onSeriesDoubleClick
                ? (event) => {
                    event.stopPropagation();
                    onSeriesDoubleClick(event);
                  }
                : undefined
            }
          >
            <span className={cn.legendSwatch} style={{ background: entry.color }} aria-hidden />
            <span>{entry.name}</span>
          </li>
        );
      })}
      <ChartPartResizeHandles
        visible={showResize}
        onResizePointerDown={(handle, event) => {
          interaction?.onPartResizePointerDown?.(ref, event, handle);
        }}
      />
    </ul>
  );
}
