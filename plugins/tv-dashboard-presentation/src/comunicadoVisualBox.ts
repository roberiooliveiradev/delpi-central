import type { CSSProperties } from "react";

import { DECK_SHAPE_DEFAULTS, resolvePaintTextColor } from "@delpi/plugin-ui/index";

import type {
  ComunicadoBlock,
  ComunicadoShapeBlock,
  ComunicadoShapeKind,
  ComunicadoTextBlock,
  ComunicadoVerticalAlign,
} from "./comunicadoTypes";
import {
  defaultStrokeWidthForPrimitive,
  resolveShapePrimitive,
  type ComunicadoVisualPrimitive,
} from "./comunicadoVisualPrimitive";

/**
 * Modo tipográfico vs. geométrico.
 * Texto/título também desenham chrome de forma (retângulo transparente por padrão).
 */
export type ComunicadoVisualBoxMode = "text" | "shape";

export type ComunicadoVisualBoxBlock = ComunicadoTextBlock | ComunicadoShapeBlock;

export type ComunicadoVisualBoxProfile = {
  mode: ComunicadoVisualBoxMode;
  /** heading | text no modo texto; kind da forma no modo shape. */
  variant: "heading" | "text" | ComunicadoShapeKind;
  /** Kind geométrico canônico — texto padrão `rectangle`. */
  shapeKind: ComunicadoShapeKind;
  /** Primitivo geométrico. */
  primitive: ComunicadoVisualPrimitive;
  /** Tag semântica do conteúdo interno. */
  textTag: "h1" | "p" | "span";
  /** Bloco com contentRuns / tipografia rica (heading/text). */
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

const TEXT_BOX_CHROME_DEFAULTS = {
  fill: "transparent",
  stroke: "transparent",
  strokeWidth: 0,
} as const;

const DEFAULT_TEXT_SHAPE_KIND: ComunicadoShapeKind = "rectangle";

export function isComunicadoVisualBoxBlock(
  block: ComunicadoBlock,
): block is ComunicadoVisualBoxBlock {
  return block.type === "heading" || block.type === "text" || block.type === "shape";
}

/** Kind geométrico da caixa visual — texto omitido → retângulo. */
export function resolveVisualBoxShapeKind(block: ComunicadoVisualBoxBlock): ComunicadoShapeKind {
  if (block.type === "shape") return block.shape;
  return block.shape ?? DEFAULT_TEXT_SHAPE_KIND;
}

export function resolveVisualBoxProfile(block: ComunicadoVisualBoxBlock): ComunicadoVisualBoxProfile {
  const shapeKind = resolveVisualBoxShapeKind(block);
  const primitive = resolveShapePrimitive(shapeKind);

  if (block.type === "heading") {
    return {
      mode: "text",
      variant: "heading",
      shapeKind,
      primitive,
      textTag: "h1",
      isRichTextBlock: true,
    };
  }
  if (block.type === "text") {
    return {
      mode: "text",
      variant: "text",
      shapeKind,
      primitive,
      textTag: "p",
      isRichTextBlock: true,
    };
  }
  return {
    mode: "shape",
    variant: shapeKind,
    shapeKind,
    primitive,
    textTag: "span",
    isRichTextBlock: false,
  };
}

export function resolveVisualBoxChrome(block: ComunicadoVisualBoxBlock): ComunicadoVisualBoxChrome {
  const profile = resolveVisualBoxProfile(block);
  const style = block.style ?? {};
  const shapeKind = profile.shapeKind;
  const primitive = profile.primitive;
  const isTextChrome = profile.mode === "text";

  const fill = isTextChrome
    ? (style.fill ?? style.backgroundColor ?? TEXT_BOX_CHROME_DEFAULTS.fill)
    : (style.fill ?? DECK_SHAPE_DEFAULTS.fill);
  const stroke = isTextChrome
    ? (style.stroke ?? style.borderColor ?? TEXT_BOX_CHROME_DEFAULTS.stroke)
    : (style.stroke ??
      (primitive === "line" ? DECK_SHAPE_DEFAULTS.lineStroke : DECK_SHAPE_DEFAULTS.stroke));
  const strokeWidth = isTextChrome
    ? (style.strokeWidth ?? style.borderWidth ?? TEXT_BOX_CHROME_DEFAULTS.strokeWidth)
    : primitive === "point"
      ? 0
      : (style.strokeWidth ?? defaultStrokeWidthForPrimitive(primitive));

  return {
    showShapeGraphic: true,
    fill,
    stroke,
    strokeWidth,
    borderRadius: style.borderRadius,
    shapeKind,
  };
}

export function visualBoxSupportsTextFormatting(block: ComunicadoVisualBoxBlock): boolean {
  return resolveVisualBoxProfile(block).isRichTextBlock || Boolean(block.content?.trim());
}

/** Qualquer caixa visual admite chrome de forma (texto = forma sem fundo). */
export function visualBoxSupportsShapeFormatting(_block: ComunicadoVisualBoxBlock): boolean {
  return true;
}

/** Palco do editor: duplo clique para editar texto interno (heading, text, shape). */
export function visualBoxSupportsInlineTextEditing(block: ComunicadoVisualBoxBlock): boolean {
  return true;
}

/**
 * Converte forma em bloco de texto rico preservando kind geométrico e estilo —
 * lista / estilo nomeado exigem contentRuns.
 */
export function visualBoxEnsureRichTextBlock(
  block: ComunicadoVisualBoxBlock,
): ComunicadoTextBlock {
  if (block.type === "heading" || block.type === "text") return block;
  return {
    id: block.id,
    type: "text",
    content: block.content ?? "",
    frame: block.frame,
    style: block.style,
    shape: block.shape,
    href: block.href,
    linkTarget: block.linkTarget,
    groupId: block.groupId,
    animations: block.animations,
  };
}

export function visualBoxBlockModifierClasses(block: ComunicadoVisualBoxBlock): string[] {
  const profile = resolveVisualBoxProfile(block);
  const primitive = profile.primitive;
  const classes = [
    `tdp-comunicado__block--${block.type}`,
    "tdp-comunicado__visual-box--shape",
    `tdp-comunicado__visual-box--primitive-${primitive}`,
  ];
  if (profile.mode === "text") {
    classes.push("tdp-comunicado__visual-box--text");
  }
  return classes;
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
  options?: { fontScale?: number; editorInteractive?: boolean },
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

  /* Texto na forma: layout absoluto sobre o gráfico — mesmo path para text e shape. */
  const textAlign = style.textAlign ?? (profile.mode === "text" ? undefined : "center");
  const verticalAlign = style.verticalAlign ?? defaultVerticalAlignForVisualBox(block);
  if (profile.mode === "text") {
    css.alignItems = "stretch";
    css.justifyContent = comunicadoVerticalAlignToJustifyContent(verticalAlign);
    if (style.textAlign) css.textAlign = style.textAlign;
    css.position = "absolute";
    css.inset = 0;
    css.padding = "0.4em";
    css.pointerEvents = options?.editorInteractive ? "auto" : "none";
  } else {
    css.alignItems =
      textAlign === "left" ? "flex-start" : textAlign === "right" ? "flex-end" : "center";
    css.justifyContent = comunicadoVerticalAlignToJustifyContent(verticalAlign);
    css.position = "absolute";
    css.inset = 0;
    css.padding = "0.4em";
    if (textAlign) css.textAlign = textAlign;
    css.pointerEvents = options?.editorInteractive ? "auto" : "none";
  }

  if (style.fontSize) css.fontSize = `${Math.max(8, style.fontSize * fontScale)}px`;
  const fillForContrast =
    style.fill && style.fill !== "transparent"
      ? style.fill
      : style.backgroundColor && style.backgroundColor !== "transparent"
        ? style.backgroundColor
        : profile.mode === "shape"
          ? DECK_SHAPE_DEFAULTS.fill
          : "#ffffff";
  const paintColor = resolvePaintTextColor(style.color, fillForContrast, {
    unsetIsAutomatic: false,
  });
  if (paintColor) css.color = paintColor;
  else if (style.color && style.color !== "auto") css.color = style.color;
  if (style.fontFamily) css.fontFamily = style.fontFamily;
  if (style.fontWeight) css.fontWeight = style.fontWeight;
  if (style.fontStyle) css.fontStyle = style.fontStyle;
  if (style.textDecoration) css.textDecoration = style.textDecoration;

  return css;
}
