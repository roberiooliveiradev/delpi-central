import { useEffect, useRef, type CSSProperties } from "react";

import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  chartPartDomProps,
  chartPartTypographyStyle,
  isChartPartInteractionSelected,
  isChartPartRefEqual,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";

export type ChartAxisTitleProps = {
  axis: "x" | "y";
  title?: string;
  visible?: boolean;
  /** Centro do título no sistema de coordenadas do SVG. */
  x: number;
  y: number;
  /** Largura/altura do foreignObject de edição. */
  editWidth: number;
  editHeight: number;
  /** Âncora do texto SVG estático. */
  textAnchor?: "start" | "middle" | "end";
  /** Rotação SVG do rótulo estático (eixo Y). */
  rotate?: string;
  interaction?: SeriesChartInteraction | null;
  chartParts?: ChartPartsMap | null;
};

/**
 * Título de eixo selecionável + editável (foreignObject contentEditable).
 * O `<text>` SVG sozinho não aceita digitação — paridade com ChartTitle.
 */
export function ChartAxisTitle({
  axis,
  title,
  visible = true,
  x,
  y,
  editWidth,
  editHeight,
  textAnchor = "middle",
  rotate,
  interaction,
  chartParts,
}: ChartAxisTitleProps) {
  const cn = useSeriesChartClasses();
  const titleRef = { kind: "axisTitle" as const, axis };
  const interactive = Boolean(interaction?.onPartPointerDown || interaction?.onPartDoubleClick);
  const selected = isChartPartInteractionSelected(titleRef, interaction?.selectedPart);
  const editing = isChartPartRefEqual(titleRef, interaction?.editingPart);
  const titleTypography = chartPartTypographyStyle(chartParts, titleRef);
  const editRef = useRef<HTMLDivElement>(null);
  const display = title?.trim() ?? "";

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
  if (!display && !editing) return null;

  const commit = () => {
    const next = (editRef.current?.textContent ?? "").replace(/\u00a0/g, " ").trim();
    interaction?.onPartContentCommit?.(titleRef, next);
  };

  const className = [
    cn.axisTitle,
    axis === "x" ? cn.axisTitleX : cn.axisTitleY,
    selected ? `${cn.root}__part--selected` : "",
    editing ? `${cn.root}__part--editing` : "",
  ]
    .filter(Boolean)
    .join(" ");

  if (editing) {
    const foX = axis === "y" ? Math.max(0, x - editWidth / 2) : x - editWidth / 2;
    const foY = axis === "y" ? y - editHeight / 2 : Math.max(0, y - editHeight + 4);
    const editStyle: CSSProperties = {
      width: "100%",
      height: "100%",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      boxSizing: "border-box",
      outline: "none",
      cursor: "text",
      fontWeight: 600,
      fontSize: "inherit",
      color: "inherit",
      whiteSpace: "nowrap",
      ...(axis === "y"
        ? { writingMode: "vertical-rl", transform: "rotate(180deg)" }
        : {}),
      ...(titleTypography as CSSProperties | undefined),
    };

    return (
      <foreignObject
        x={foX}
        y={foY}
        width={Math.max(editWidth, 24)}
        height={Math.max(editHeight, 20)}
        className={className}
        {...chartPartDomProps(titleRef, interaction?.selectedPart)}
        onPointerDown={(event) => {
          event.stopPropagation();
        }}
      >
        <div
          ref={editRef}
          // xmlns necessário em alguns browsers para foreignObject HTML
          xmlns="http://www.w3.org/1999/xhtml"
          contentEditable
          suppressContentEditableWarning
          role="textbox"
          aria-label={axis === "x" ? "Editar título do eixo X" : "Editar título do eixo Y"}
          style={editStyle}
          onBlur={() => commit()}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              commit();
            } else if (event.key === "Escape") {
              event.preventDefault();
              interaction?.onPartEditCancel?.();
            }
          }}
        >
          {display || "\u00a0"}
        </div>
      </foreignObject>
    );
  }

  return (
    <text
      x={x}
      y={y}
      className={className}
      textAnchor={textAnchor}
      transform={rotate}
      style={titleTypography}
      {...chartPartDomProps(titleRef, interaction?.selectedPart)}
      onPointerDown={
        interactive
          ? (event) => {
              event.stopPropagation();
              interaction?.onPartPointerDown?.(titleRef, event);
            }
          : undefined
      }
      onDoubleClick={
        interactive
          ? (event) => {
              event.stopPropagation();
              event.preventDefault();
              interaction?.onPartDoubleClick?.(titleRef, event);
            }
          : undefined
      }
    >
      {display}
    </text>
  );
}
