import { useEffect, useRef } from "react";

import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  chartPartDomProps,
  isChartPartRefEqual,
  type SeriesChartInteraction,
} from "../seriesChartParts";

export type ChartTitleProps = {
  title?: string;
  visible?: boolean;
  interaction?: SeriesChartInteraction | null;
};

export function ChartTitle({ title, visible = true, interaction }: ChartTitleProps) {
  const cn = useSeriesChartClasses();
  const ref = { kind: "title" as const };
  const selected = isChartPartRefEqual(ref, interaction?.selectedPart);
  const editing = isChartPartRefEqual(ref, interaction?.editingPart);
  const interactive = Boolean(interaction?.onPartPointerDown);
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
        selected ? `${cn.root}__part--selected` : "",
        editing ? `${cn.root}__part--editing` : "",
      ]
        .filter(Boolean)
        .join(" ")}
      {...chartPartDomProps(ref, interaction?.selectedPart)}
      contentEditable={editing || undefined}
      suppressContentEditableWarning={editing || undefined}
      role={editing ? "textbox" : undefined}
      aria-label={editing ? "Editar título do gráfico" : undefined}
      onPointerDown={
        interactive
          ? (event) => {
              if (editing) {
                event.stopPropagation();
                return;
              }
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
