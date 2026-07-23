import { useEffect, useRef, type CSSProperties } from "react";

import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  bindChartPartPointer,
  chartPartAllowsResize,
  chartPartTypographyStyle,
  getChartPartState,
  looksLikeAutoMaterializedFlowFrame,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import { applyTextEffectStyleToCss } from "../../shape/textEffectStyle";
import { resolvePaintTextColor } from "../../shape/colorUtils";
import { DECK_COLOR_TEXT_STRONG, DECK_COLOR_SURFACE } from "../../../theme/deckColorCatalog";
import {
  DeckContentRunsView,
  plainTextFromDeckContentRuns,
  shouldPersistDeckContentRuns,
} from "../../rich-text/deckContentRuns";
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
  const rawFrame = getChartPartState(chartParts, ref)?.frame;
  const frame =
    rawFrame && looksLikeAutoMaterializedFlowFrame("title", rawFrame) ? undefined : rawFrame;
  const partState = getChartPartState(chartParts, ref);
  const partStyle = partState?.style;
  const contentRuns = partState?.contentRuns;
  const pointer = bindChartPartPointer(ref, interaction);
  const { selected, editing, onPointerDown, onDoubleClick, ...dom } = pointer;
  const frameStyle = partFrameStyle(frame, selected && !editing);
  const showResize = selected && !editing && chartPartAllowsResize(ref);
  const chartAreaFill =
    getChartPartState(chartParts, { kind: "chartArea" })?.style?.fill ?? DECK_COLOR_SURFACE;
  const typography = chartPartTypographyStyle(chartParts, ref, { boxLayout: true });
  const textStyle: CSSProperties = {
    ...frameStyle,
    ...typography,
    color:
      resolvePaintTextColor(partStyle?.color, chartAreaFill) ??
      typography?.color ??
      DECK_COLOR_TEXT_STRONG,
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

  useEffect(() => {
    if (!editing || !editRef.current) return;
    const el = editRef.current;
    interaction?.onPartEditableMount?.(ref, el);
    const display = title?.trim() ?? "";
    if (interaction?.renderPartEditorHtml) {
      el.innerHTML = interaction.renderPartEditorHtml(ref, display, contentRuns);
    } else {
      el.textContent = display || "\u00a0";
    }
    el.focus();
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(el);
    selection?.removeAllRanges();
    selection?.addRange(range);
    return () => interaction?.onPartEditableMount?.(ref, null);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- seed only when entering edit
  }, [editing]);

  if (!visible) return null;
  if (!title?.trim() && !editing && !contentRuns?.length) return null;

  const display = title?.trim() ?? "";

  const commit = () => {
    const el = editRef.current;
    if (!el) return;
    const runs = interaction?.parsePartEditorRuns?.(ref, el);
    const next = runs
      ? plainTextFromDeckContentRuns(runs).replace(/\u00a0/g, " ").trim()
      : (el.textContent ?? "").replace(/\u00a0/g, " ").trim();
    const meta =
      runs && shouldPersistDeckContentRuns(runs)
        ? { contentRuns: runs }
        : runs
          ? { contentRuns: undefined }
          : undefined;
    interaction?.onPartContentCommit?.(ref, next, meta);
  };

  const className = [
    cn.title,
    frameStyle?.position === "absolute" ? `${cn.root}__part--framed` : "",
    selected ? `${cn.root}__part--selected` : "",
    editing ? `${cn.root}__part--editing` : "",
    showResize ? `${cn.root}__part--resizable` : "",
  ]
    .filter(Boolean)
    .join(" ");

  /* Árvore separada na edição: evita React limpar o contentEditable em re-render. */
  if (editing) {
    return (
      <div
        ref={editRef}
        className={className}
        style={textStyle}
        {...dom}
        contentEditable
        suppressContentEditableWarning
        role="textbox"
        aria-label="Editar título do gráfico"
        onPointerDown={onPointerDown}
        onDoubleClick={onDoubleClick}
        onBlur={commit}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            commit();
          } else if (event.key === "Escape") {
            event.preventDefault();
            interaction?.onPartEditCancel?.();
          }
        }}
      />
    );
  }

  return (
    <div
      ref={hostRef}
      className={className}
      style={textStyle}
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    >
      <DeckContentRunsView content={display} contentRuns={contentRuns} />
      <ChartPartResizeHandles
        visible={showResize}
        onResizePointerDown={(handle, event) => {
          interaction?.onPartResizePointerDown?.(ref, event, handle);
        }}
      />
    </div>
  );
}
