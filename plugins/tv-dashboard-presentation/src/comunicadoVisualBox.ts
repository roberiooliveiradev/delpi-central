import type { CSSProperties } from "react";

import type {
  ComunicadoBlock,
  ComunicadoShapeBlock,
  ComunicadoShapeKind,
  ComunicadoTextBlock,
  ComunicadoVerticalAlign,
} from "./comunicadoTypes";

/** Modo visual da caixa — texto sem preenchimento/contorno; forma com chrome gráfico. */
export type ComunicadoVisualBoxMode = "text" | "shape";

export type ComunicadoVisualBoxBlock = ComunicadoTextBlock | ComunicadoShapeBlock;

export type ComunicadoVisualBoxProfile = {
  mode: ComunicadoVisualBoxMode;
  /** heading | text no modo texto; kind da forma no modo shape. */
  variant: "heading" | "text" | ComunicadoShapeKind;
  /** Tag semântica do conteúdo interno. */
  textTag: "h1" | "p" | "span";
  /** Bloco de texto com contentRuns ou heading/text (não forma com texto plano). */
  isRichTextBlock: boolean;
};

export type ComunicadoVisualBoxChrome = {
  showShapeGraphic: boolean;
  fill: string;
  stroke: string;
  strokeWidth: number;
  borderRadius?: number;
  shapeKind?: ComunicadoShapeKind;
};

const TEXT_BOX_DEFAULTS = {
  fill: "transparent",
  stroke: "transparent",
  strokeWidth: 0,
} as const;

export function isComunicadoVisualBoxBlock(
  block: ComunicadoBlock,
): block is ComunicadoVisualBoxBlock {
  return block.type === "heading" || block.type === "text" || block.type === "shape";
}

export function resolveVisualBoxProfile(block: ComunicadoVisualBoxBlock): ComunicadoVisualBoxProfile {
  if (block.type === "heading") {
    return { mode: "text", variant: "heading", textTag: "h1", isRichTextBlock: true };
  }
  if (block.type === "text") {
    return { mode: "text", variant: "text", textTag: "p", isRichTextBlock: true };
  }
  return {
    mode: "shape",
    variant: block.shape,
    textTag: "span",
    isRichTextBlock: false,
  };
}

export function resolveVisualBoxChrome(block: ComunicadoVisualBoxBlock): ComunicadoVisualBoxChrome {
  const profile = resolveVisualBoxProfile(block);
  if (profile.mode === "text") {
    return { showShapeGraphic: false, ...TEXT_BOX_DEFAULTS };
  }

  const style = block.style ?? {};
  const shape = block.shape;
  return {
    showShapeGraphic: true,
    fill: style.fill ?? "#089bdb",
    stroke: style.stroke ?? "#ffffff",
    strokeWidth:
      style.strokeWidth ??
      (shape === "line" || shape === "line-arrow-right" ? 4 : 2),
    borderRadius: style.borderRadius,
    shapeKind: shape,
  };
}

export function visualBoxSupportsTextFormatting(block: ComunicadoVisualBoxBlock): boolean {
  return resolveVisualBoxProfile(block).mode === "text";
}

export function visualBoxSupportsShapeFormatting(block: ComunicadoVisualBoxBlock): boolean {
  return resolveVisualBoxProfile(block).mode === "shape";
}

export function visualBoxBlockModifierClasses(block: ComunicadoVisualBoxBlock): string[] {
  const profile = resolveVisualBoxProfile(block);
  if (profile.mode === "text") {
    return [`tdp-comunicado__block--${block.type}`, "tdp-comunicado__visual-box--text"];
  }
  return ["tdp-comunicado__block--shape", "tdp-comunicado__visual-box--shape"];
}

export function comunicadoVerticalAlignToJustifyContent(
  verticalAlign: ComunicadoVerticalAlign,
): NonNullable<CSSProperties["justifyContent"]> {
  if (verticalAlign === "middle") return "center";
  if (verticalAlign === "bottom") return "flex-end";
  return "flex-start";
}

export function defaultVerticalAlignForVisualBox(
  block: ComunicadoVisualBoxBlock,
): ComunicadoVerticalAlign {
  if (block.type === "heading") return "middle";
  if (block.type === "text") return "top";
  return "middle";
}

/** Estilos do contêiner flex da caixa visual (texto e forma com texto). */
export function resolveVisualBoxContentLayoutStyle(
  block: ComunicadoVisualBoxBlock,
  options?: { fontScale?: number },
): CSSProperties {
  const fontScale = options?.fontScale ?? 1;
  const style = block.style ?? {};
  const profile = resolveVisualBoxProfile(block);
  const css: CSSProperties = {
    display: "flex",
    flexDirection: "column",
    width: "100%",
    height: "100%",
    boxSizing: "border-box",
  };

  if (profile.mode === "text") {
    css.alignItems = "stretch";
    const verticalAlign = style.verticalAlign ?? defaultVerticalAlignForVisualBox(block);
    css.justifyContent = comunicadoVerticalAlignToJustifyContent(verticalAlign);
    if (style.textAlign) css.textAlign = style.textAlign;
  } else {
    css.alignItems = "center";
    css.justifyContent = "center";
    css.position = "absolute";
    css.inset = 0;
    css.padding = "0.4em";
    css.textAlign = style.textAlign ?? "center";
    css.pointerEvents = "none";
  }

  if (style.fontSize) css.fontSize = `${Math.max(8, style.fontSize * fontScale)}px`;
  if (style.color) css.color = style.color;
  if (style.fontFamily) css.fontFamily = style.fontFamily;
  if (style.fontWeight) css.fontWeight = style.fontWeight;
  if (style.fontStyle) css.fontStyle = style.fontStyle;
  if (style.textDecoration) css.textDecoration = style.textDecoration;

  return css;
}
