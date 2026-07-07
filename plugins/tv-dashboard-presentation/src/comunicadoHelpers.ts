import type { CSSProperties } from "react";

import type {
  ComunicadoBackground,
  ComunicadoBlock,
  ComunicadoBlockStyle,
  ComunicadoConfig,
  ComunicadoFrame,
  ComunicadoShapeKind,
  ComunicadoTextDecoration,
  ComunicadoVerticalAlign,
} from "./comunicadoTypes";
import {
  COMUNICADO_FONT_SIZE_MAX,
  COMUNICADO_FONT_SIZE_MIN,
} from "./comunicadoTypes";

export function newBlockId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `block-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

const DEFAULT_BACKGROUND: ComunicadoBackground = { type: "color", value: "#0f172a" };
const DEFAULT_HEADLINE = "Título";

export function defaultFrame(type: ComunicadoBlock["type"], shape?: ComunicadoShapeKind): ComunicadoFrame {
  if (type === "heading") return { x: 5, y: 12, w: 90, h: 18 };
  if (type === "text") return { x: 5, y: 34, w: 90, h: 14 };
  if (type === "image") return { x: 10, y: 22, w: 80, h: 56 };
  if (type === "video") return { x: 5, y: 15, w: 90, h: 70 };
  if (shape === "line") return { x: 10, y: 48, w: 80, h: 2 };
  if (shape === "arrow-right") return { x: 35, y: 40, w: 30, h: 20 };
  return { x: 30, y: 30, w: 40, h: 40 };
}

export function defaultStyle(type: ComunicadoBlock["type"], shape?: ComunicadoShapeKind) {
  if (type === "heading") {
    return {
      fontSize: 56,
      color: "#ffffff",
      fontFamily: "Inter, system-ui, sans-serif",
      textAlign: "center" as const,
      verticalAlign: "middle" as const,
      lineHeight: 1.15,
      fontWeight: "bold" as const,
      zIndex: 2,
    };
  }
  if (type === "text") {
    return {
      fontSize: 28,
      color: "#cbd5e1",
      fontFamily: "Inter, system-ui, sans-serif",
      textAlign: "center" as const,
      verticalAlign: "top" as const,
      lineHeight: 1.15,
      fontWeight: "normal" as const,
      zIndex: 2,
    };
  }
  if (type === "image" || type === "video") {
    return { objectFit: "contain" as const, zIndex: 1 };
  }
  if (type === "shape") {
    const base = {
      zIndex: 1,
      fill: "#089bdb",
      stroke: "#ffffff",
      strokeWidth: shape === "line" ? 4 : 2,
      opacity: shape === "line" ? 1 : 0.9,
    };
    if (shape === "rounded-rect") return { ...base, borderRadius: 16 };
    if (shape === "ellipse") return { ...base, borderRadius: 9999 };
    return base;
  }
  return {};
}

export function createBlock(
  type: ComunicadoBlock["type"],
  content = "",
  shape?: ComunicadoShapeKind,
): ComunicadoBlock {
  const base = {
    id: newBlockId(),
    type,
    frame: defaultFrame(type, shape),
    style: defaultStyle(type, shape),
  };
  if (type === "heading" || type === "text") {
    return { ...base, type, content };
  }
  if (type === "shape") {
    const kind = shape ?? "rectangle";
    return { ...base, type, shape: kind, content: content || "" };
  }
  return { ...base, type };
}

export function createShapeBlock(shape: ComunicadoShapeKind): ComunicadoBlock {
  return createBlock("shape", "", shape);
}

export function parseComunicadoConfig(raw: Record<string, unknown> | undefined | null): ComunicadoConfig {
  const cfg = raw ?? {};
  const blocks = Array.isArray(cfg.blocks) ? (cfg.blocks as ComunicadoBlock[]) : [];
  if (blocks.length > 0) {
    return {
      version: Number(cfg.version) || detectConfigVersion(blocks),
      headline: String(cfg.headline ?? ""),
      subtitle: String(cfg.subtitle ?? ""),
      background: normalizeBackground(cfg.background),
      blocks: blocks.map(normalizeBlock),
    };
  }
  const headline = String(cfg.headline ?? DEFAULT_HEADLINE);
  const subtitle = String(cfg.subtitle ?? "");
  return {
    version: 2,
    headline,
    subtitle,
    background: DEFAULT_BACKGROUND,
    blocks: [
      createBlock("heading", headline),
      ...(subtitle ? [createBlock("text", subtitle)] : []),
    ],
  };
}

function detectConfigVersion(blocks: ComunicadoBlock[]): number {
  const hasV3 = blocks.some((block) => {
    if (block.type === "shape") return true;
    if ((block.type === "heading" || block.type === "text") && block.href) return true;
    const style = block.style ?? {};
    return Boolean(
      style.fontFamily ||
        style.fontStyle ||
        style.textDecoration ||
        style.rotation ||
        style.fill ||
        style.stroke,
    );
  });
  return hasV3 ? 3 : 2;
}

export function serializeComunicadoConfig(config: ComunicadoConfig): Record<string, unknown> {
  const headingBlock = config.blocks?.find((b) => b.type === "heading");
  const textBlock = config.blocks?.find((b) => b.type === "text");
  const background = config.background ?? DEFAULT_BACKGROUND;
  const serializedBackground =
    background.type === "image"
      ? { type: "image", assetId: background.assetId }
      : { type: "color", value: background.value || "#0f172a" };
  const blocks = (config.blocks ?? []).map(serializeBlock);
  const version = config.version ?? detectConfigVersion(config.blocks ?? []);
  return {
    version,
    headline:
      headingBlock && "content" in headingBlock
        ? headingBlock.content
        : config.headline ?? DEFAULT_HEADLINE,
    subtitle: textBlock && "content" in textBlock ? textBlock.content : config.subtitle ?? "",
    background: serializedBackground,
    blocks,
  };
}

function serializeBlock(block: ComunicadoBlock): Record<string, unknown> {
  const base: Record<string, unknown> = {
    id: block.id,
    type: block.type,
    frame: block.frame,
    style: block.style ?? {},
  };
  if (block.type === "heading" || block.type === "text") {
    base.content = block.content;
    if (block.href) base.href = block.href;
    if (block.linkTarget) base.linkTarget = block.linkTarget;
  } else if (block.type === "image" || block.type === "video") {
    base.assetId = block.assetId;
  } else if (block.type === "shape") {
    base.shape = block.shape;
    if (block.content) base.content = block.content;
  }
  return base;
}

function normalizeBackground(value: unknown): ComunicadoBackground {
  if (!value || typeof value !== "object") return DEFAULT_BACKGROUND;
  const bg = value as Record<string, unknown>;
  if (bg.type === "image") {
    return {
      type: "image",
      assetId: typeof bg.assetId === "string" ? bg.assetId : undefined,
      url: typeof bg.url === "string" ? bg.url : undefined,
      value: typeof bg.value === "string" ? bg.value : undefined,
    };
  }
  const color = typeof bg.value === "string" && bg.value.trim() ? bg.value : "#0f172a";
  return { type: "color", value: color };
}

function normalizeBlock(value: unknown): ComunicadoBlock {
  if (!value || typeof value !== "object") {
    return createBlock("text", "");
  }
  const block = value as Record<string, unknown>;
  const type = (block.type as ComunicadoBlock["type"]) ?? "text";
  const frame = normalizeFrame(block.frame, type);
  const shape = typeof block.shape === "string" ? (block.shape as ComunicadoShapeKind) : undefined;
  const style = (block.style as ComunicadoBlock["style"]) ?? defaultStyle(type, shape);
  const id = typeof block.id === "string" ? block.id : newBlockId();
  if (type === "heading" || type === "text") {
    return {
      id,
      type,
      frame,
      style,
      content: String(block.content ?? ""),
      href: typeof block.href === "string" && block.href.trim() ? block.href.trim() : undefined,
      linkTarget: block.linkTarget === "_self" ? "_self" : block.linkTarget === "_blank" ? "_blank" : undefined,
    };
  }
  if (type === "shape") {
    const kind = shape && isShapeKind(shape) ? shape : "rectangle";
    return {
      id,
      type,
      frame,
      style: { ...defaultStyle("shape", kind), ...style },
      shape: kind,
      content: typeof block.content === "string" ? block.content : "",
    };
  }
  return {
    id,
    type,
    frame,
    style,
    assetId: typeof block.assetId === "string" ? block.assetId : undefined,
    url: typeof block.url === "string" ? block.url : undefined,
  };
}

function isShapeKind(value: string): value is ComunicadoShapeKind {
  return ["rectangle", "rounded-rect", "ellipse", "triangle", "arrow-right", "line"].includes(value);
}

function normalizeFrame(value: unknown, type: ComunicadoBlock["type"]): ComunicadoFrame {
  if (!value || typeof value !== "object") return defaultFrame(type);
  const frame = value as Record<string, unknown>;
  const num = (key: keyof ComunicadoFrame, fallback: number) => {
    const raw = frame[key];
    const parsed = typeof raw === "number" ? raw : Number(raw);
    return Number.isFinite(parsed) ? parsed : fallback;
  };
  return {
    x: Math.max(0, Math.min(100, num("x", 5))),
    y: Math.max(0, Math.min(100, num("y", 10))),
    w: Math.max(2, Math.min(100, num("w", 90))),
    h: Math.max(1, Math.min(100, num("h", 20))),
  };
}

export function frameStyle(frame: ComunicadoFrame): CSSProperties {
  return {
    left: `${frame.x}%`,
    top: `${frame.y}%`,
    width: `${frame.w}%`,
    height: `${frame.h}%`,
  };
}

/** h1/p usam text-align: inherit no contêiner flex em coluna. */
export function comunicadoVerticalAlignToJustifyContent(
  verticalAlign: ComunicadoVerticalAlign,
): NonNullable<CSSProperties["justifyContent"]> {
  if (verticalAlign === "middle") return "center";
  if (verticalAlign === "bottom") return "flex-end";
  return "flex-start";
}

export function defaultVerticalAlignForBlock(type: "heading" | "text"): ComunicadoVerticalAlign {
  return type === "heading" ? "middle" : "top";
}

export function defaultTextBlockStyle(type: "heading" | "text"): ComunicadoBlockStyle {
  return { ...(defaultStyle(type) as ComunicadoBlockStyle) };
}

export function clampFontSize(size: number): number {
  return Math.max(
    COMUNICADO_FONT_SIZE_MIN,
    Math.min(COMUNICADO_FONT_SIZE_MAX, Math.round(size)),
  );
}

export function parseTextDecorationFlags(
  value?: ComunicadoTextDecoration,
): { underline: boolean; strikethrough: boolean } {
  return {
    underline: value?.includes("underline") ?? false,
    strikethrough: value?.includes("line-through") ?? false,
  };
}

export function buildTextDecoration(
  underline: boolean,
  strikethrough: boolean,
): ComunicadoTextDecoration {
  if (underline && strikethrough) return "underline line-through";
  if (underline) return "underline";
  if (strikethrough) return "line-through";
  return "none";
}

export function comunicadoTextInnerStyle(
  block: Extract<ComunicadoBlock, { type: "heading" } | { type: "text" }>,
  options?: { fontScale?: number },
): CSSProperties {
  const fontScale = options?.fontScale ?? 1;
  const style = block.style ?? {};
  const css: CSSProperties = {};

  if (style.lineHeight != null) css.lineHeight = style.lineHeight;
  if (style.letterSpacing != null) css.letterSpacing = `${style.letterSpacing}px`;
  if (style.textHighlight) css.backgroundColor = style.textHighlight;
  if (style.textDecoration) css.textDecoration = style.textDecoration;
  if (style.fontSize) css.fontSize = `${Math.max(8, style.fontSize * fontScale)}px`;
  if (style.color) css.color = style.color;
  if (style.fontFamily) css.fontFamily = style.fontFamily;
  if (style.fontWeight) css.fontWeight = style.fontWeight;
  if (style.fontStyle) css.fontStyle = style.fontStyle;

  return css;
}

export function blockCssStyle(block: ComunicadoBlock, options?: { fontScale?: number }): CSSProperties {
  const fontScale = options?.fontScale ?? 1;
  const style = block.style ?? {};
  const css: CSSProperties = {
    ...frameStyle(block.frame),
    zIndex: style.zIndex ?? 1,
    opacity: style.opacity ?? 1,
    ...(style.rotation ? { transform: `rotate(${style.rotation}deg)` } : {}),
  };

  if (block.type === "heading" || block.type === "text") {
    css.display = "flex";
    css.flexDirection = "column";
    css.alignItems = "stretch";
    const verticalAlign = style.verticalAlign ?? defaultVerticalAlignForBlock(block.type);
    css.justifyContent = comunicadoVerticalAlignToJustifyContent(verticalAlign);
    if (style.textAlign) css.textAlign = style.textAlign;
    if (style.fontSize) css.fontSize = `${Math.max(8, style.fontSize * fontScale)}px`;
    if (style.color) css.color = style.color;
    if (style.fontFamily) css.fontFamily = style.fontFamily;
    if (style.fontWeight) css.fontWeight = style.fontWeight;
    if (style.fontStyle) css.fontStyle = style.fontStyle;
    if (style.lineHeight != null) css.lineHeight = style.lineHeight;
    return css;
  }

  if (block.type === "shape" && block.content) {
    if (style.fontSize) css.fontSize = `${Math.max(8, style.fontSize * fontScale)}px`;
    if (style.color) css.color = style.color;
    if (style.fontFamily) css.fontFamily = style.fontFamily;
    if (style.textAlign) css.textAlign = style.textAlign;
    if (style.fontWeight) css.fontWeight = style.fontWeight;
    if (style.fontStyle) css.fontStyle = style.fontStyle;
    if (style.textDecoration) css.textDecoration = style.textDecoration;
  }

  if (block.type === "shape") {
    if (style.backgroundColor) css.backgroundColor = style.backgroundColor;
    if (style.borderColor) css.borderColor = style.borderColor;
    if (style.borderWidth != null) css.borderWidth = style.borderWidth;
    if (style.borderRadius != null) css.borderRadius = style.borderRadius;
  }

  return css;
}

export function sortBlocksByZIndex(blocks: ComunicadoBlock[]): ComunicadoBlock[] {
  return [...blocks].sort((a, b) => (a.style?.zIndex ?? 1) - (b.style?.zIndex ?? 1));
}

export function hasRichComunicado(data: ComunicadoScreenDataLike): boolean {
  return Array.isArray(data.blocks) && data.blocks.length > 0;
}

export type ComunicadoScreenDataLike = {
  blocks?: ComunicadoBlock[];
  headline?: string;
  subtitle?: string;
};

export function clampFrame(frame: ComunicadoFrame): ComunicadoFrame {
  return {
    x: Math.max(0, Math.min(100 - frame.w, frame.x)),
    y: Math.max(0, Math.min(100 - frame.h, frame.y)),
    w: Math.max(2, Math.min(100, frame.w)),
    h: Math.max(1, Math.min(100, frame.h)),
  };
}

export function nextZIndex(blocks: ComunicadoBlock[]): number {
  const max = blocks.reduce((acc, block) => Math.max(acc, block.style?.zIndex ?? 1), 0);
  return max + 1;
}
