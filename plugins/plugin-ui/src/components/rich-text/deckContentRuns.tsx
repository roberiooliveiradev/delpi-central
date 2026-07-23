import type { CSSProperties, ReactNode } from "react";

/**
 * Trecho tipográfico (paridade Google Slides TextRun / Canva RichtextRange).
 * Espelha `ComunicadoContentRun` do presentation — sem depender desse pacote.
 */
export type DeckContentRunStyle = {
  fontSize?: number;
  color?: string;
  fontFamily?: string;
  textHighlight?: string;
  fontWeight?: "normal" | "bold" | string | number;
  fontStyle?: "normal" | "italic" | string;
  textDecoration?: string;
  lineHeight?: number;
};

export type DeckContentRun = {
  text: string;
  style?: DeckContentRunStyle;
};

export function plainTextFromDeckContentRuns(runs: DeckContentRun[] | undefined): string {
  if (!runs?.length) return "";
  return runs.map((run) => run.text).join("");
}

export function shouldPersistDeckContentRuns(runs: DeckContentRun[] | undefined): boolean {
  if (!runs || runs.length === 0) return false;
  if (runs.length > 1) return true;
  return Boolean(runs[0]?.style && Object.keys(runs[0].style).length > 0);
}

function runStyleToCss(style: DeckContentRunStyle | undefined): CSSProperties {
  if (!style) return {};
  const css: CSSProperties = {};
  if (style.fontSize != null) css.fontSize = `${Math.max(8, style.fontSize)}px`;
  if (style.color) css.color = style.color;
  if (style.fontFamily) css.fontFamily = style.fontFamily;
  if (style.textHighlight) css.backgroundColor = style.textHighlight;
  if (style.fontWeight != null) css.fontWeight = style.fontWeight as CSSProperties["fontWeight"];
  if (style.fontStyle) css.fontStyle = style.fontStyle as CSSProperties["fontStyle"];
  if (style.textDecoration) css.textDecoration = style.textDecoration;
  if (style.lineHeight != null) css.lineHeight = style.lineHeight;
  return css;
}

/** Paint readonly de runs — único caminho rico no kit (KPI/chart/input). */
export function DeckContentRunsView({
  content,
  contentRuns,
  className,
  style,
  as: Tag = "span",
}: {
  content?: string;
  contentRuns?: DeckContentRun[];
  className?: string;
  style?: CSSProperties;
  as?: "span" | "p" | "div";
}): ReactNode {
  const runs =
    contentRuns && contentRuns.length > 0
      ? contentRuns
      : content != null
        ? [{ text: content }]
        : [];
  const showRuns =
    runs.length > 1 || runs.some((run) => run.style && Object.keys(run.style).length > 0);
  if (!showRuns) {
    return (
      <Tag className={className} style={style}>
        {plainTextFromDeckContentRuns(runs) || content || ""}
      </Tag>
    );
  }
  return (
    <Tag className={className} style={style}>
      {runs.map((run, index) => (
        <span key={`${index}-${run.text.slice(0, 12)}`} style={runStyleToCss(run.style)}>
          {run.text}
        </span>
      ))}
    </Tag>
  );
}
