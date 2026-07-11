import { useEffect, useRef, type CSSProperties } from "react";

import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  bindChartPartPointer,
  getChartPartState,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";

export type ChartTitleProps = {
  title?: string;
  visible?: boolean;
  interaction?: SeriesChartInteraction | null;
  chartParts?: ChartPartsMap | null;
};

function partFrameStyle(
  frame: { x: number; y: number; w?: number; h?: number } | undefined,
): CSSProperties | undefined {
  if (!frame) return undefined;
  return {
    position: "absolute",
    left: `${frame.x}%`,
    top: `${frame.y}%`,
    width: frame.w != null ? `${frame.w}%` : "auto",
    height: frame.h != null ? `${frame.h}%` : "auto",
    zIndex: 3,
    margin: 0,
  };
}

export function ChartTitle({ title, visible = true, interaction, chartParts }: ChartTitleProps) {
  const cn = useSeriesChartClasses();
  const ref = { kind: "title" as const };
  const frame = getChartPartState(chartParts, ref)?.frame;
  const frameStyle = partFrameStyle(frame);
  const pointer = bindChartPartPointer(ref, interaction);
  const { selected, editing, onPointerDown, onDoubleClick, ...dom } = pointer;

  const editRef = useRef<HTMLDivElement>(null);

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
      ref={editing ? editRef : undefined}
      className={[
        cn.title,
        frameStyle ? `${cn.root}__part--framed` : "",
        selected ? `${cn.root}__part--selected` : "",
        editing ? `${cn.root}__part--editing` : "",
      ]
        .filter(Boolean)
        .join(" ")}
      style={frameStyle}
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
    </div>
  );
}
