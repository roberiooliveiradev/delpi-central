import { useEffect, useLayoutEffect, useRef, type CSSProperties } from "react";

import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  bindChartPartPointer,
  chartPartAllowsResize,
  clampChartPartFrame,
  getChartPartState,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import { applyTextEffectStyleToCss } from "../../shape/textEffectStyle";
import { resolvePaintTextColor } from "../../shape/colorUtils";
import { DECK_COLOR_TEXT_STRONG, DECK_COLOR_SURFACE } from "../../../theme/deckColorCatalog";
import { ChartPartResizeHandles } from "./ChartPartResizeHandles";

export type ChartTitleProps = {
  title?: string;
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

export function ChartTitle({ title, visible = true, interaction, chartParts }: ChartTitleProps) {
  const cn = useSeriesChartClasses();
  const ref = { kind: "title" as const };
  const frame = getChartPartState(chartParts, ref)?.frame;
  const partStyle = getChartPartState(chartParts, ref)?.style;
  const pointer = bindChartPartPointer(ref, interaction);
  const { selected, editing, onPointerDown, onDoubleClick, ...dom } = pointer;
  const frameStyle = partFrameStyle(frame, selected && !editing);
  const showResize = selected && !editing && chartPartAllowsResize(ref);
  const chartAreaFill =
    getChartPartState(chartParts, { kind: "chartArea" })?.style?.fill ?? DECK_COLOR_SURFACE;
  const textStyle: CSSProperties = {
    ...frameStyle,
    fontFamily: partStyle?.fontFamily,
    fontSize: partStyle?.fontSize != null ? `${partStyle.fontSize}px` : undefined,
    fontWeight: partStyle?.fontWeight,
    fontStyle: partStyle?.fontStyle,
    color: resolvePaintTextColor(partStyle?.color, chartAreaFill) ?? DECK_COLOR_TEXT_STRONG,
    ...(partStyle?.fill && partStyle.fill !== "transparent"
      ? { background: partStyle.fill }
      : {}),
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
  applyTextEffectStyleToCss(partStyle, textStyle);

  const hostRef = useRef<HTMLDivElement>(null);
  const editRef = useRef<HTMLDivElement>(null);

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
  }, [showResize, frame?.w, interaction, ref]);

  useEffect(() => {
    if (!editing || !editRef.current) return;
    editRef.current.focus();
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(editRef.current);
    selection?.removeAllRanges();
    selection?.addRange(range);
  }, [editing]);

  if (!visible) return null;
  if (!title?.trim() && !editing) return null;

  const display = title?.trim() ?? "";

  const commit = () => {
    const next = (editRef.current?.textContent ?? "").replace(/\u00a0/g, " ").trim();
    interaction?.onPartContentCommit?.(ref, next);
  };

  return (
    <div
      ref={(node) => {
        hostRef.current = node;
        if (editing) editRef.current = node;
      }}
      className={[
        cn.title,
        frameStyle?.position === "absolute" ? `${cn.root}__part--framed` : "",
        selected ? `${cn.root}__part--selected` : "",
        editing ? `${cn.root}__part--editing` : "",
        showResize ? `${cn.root}__part--resizable` : "",
      ]
        .filter(Boolean)
        .join(" ")}
      style={textStyle}
      {...dom}
      contentEditable={editing || undefined}
      suppressContentEditableWarning={editing || undefined}
      role={editing ? "textbox" : undefined}
      aria-label={editing ? "Editar título do gráfico" : undefined}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
      onBlur={
        editing
          ? () => {
              commit();
            }
          : undefined
      }
      onKeyDown={
        editing
          ? (event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                commit();
              } else if (event.key === "Escape") {
                event.preventDefault();
                interaction?.onPartEditCancel?.();
              }
            }
          : undefined
      }
    >
      {editing ? display || "\u00a0" : display}
      <ChartPartResizeHandles
        visible={showResize}
        onResizePointerDown={(handle, event) => {
          interaction?.onPartResizePointerDown?.(ref, event, handle);
        }}
      />
    </div>
  );
}
