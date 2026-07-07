import type { CSSProperties } from "react";

import type {
  ComunicadoBackground,
  ComunicadoBlock,
  ComunicadoBlockStyle,
  ComunicadoConfig,
  ComunicadoDataBinding,
  ComunicadoDataBlockType,
  ComunicadoDataFilters,
  ComunicadoDataResolved,
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

const DATA_BLOCK_TYPES = new Set(["data_kpi", "data_chart", "data_table", "data_metric"]);

export function isDataBlockType(type: string): type is ComunicadoDataBlockType {
  return DATA_BLOCK_TYPES.has(type);
}

export function mergeDataFilters(
  slideFilters?: ComunicadoDataFilters,
  blockParams?: ComunicadoDataBinding["params"],
): ComunicadoDataFilters {
  const merged: ComunicadoDataFilters = { ...(slideFilters ?? {}) };
  if (blockParams) {
    for (const [key, value] of Object.entries(blockParams)) {
      if (value !== null && value !== undefined && value !== "") {
        merged[key] = value;
      }
    }
  }
  return merged;
}

export function defaultDataBlockTypeForRoute(
  allowedModes: string[] | undefined,
): ComunicadoDataBlockType {
  const modes = allowedModes ?? [];
  if (modes.includes("kpi")) return "data_kpi";
  if (modes.includes("line_chart") || modes.includes("bar_chart")) return "data_chart";
  if (modes.includes("table")) return "data_table";
  return "data_kpi";
}

export function createDataBlock(
  operationId: string,
  options: {
    blockType?: ComunicadoDataBlockType;
    label?: string;
    displayMode?: ComunicadoDataBinding["displayMode"];
    defaultParams?: Record<string, string | number>;
  } = {},
): ComunicadoBlock {
  const blockType = options.blockType ?? "data_kpi";
  const frame =
    blockType === "data_chart"
      ? { x: 10, y: 28, w: 80, h: 45 }
      : blockType === "data_table"
        ? { x: 5, y: 55, w: 90, h: 35 }
        : { x: 5, y: 28, w: 28, h: 22 };
  return {
    id: newBlockId(),
    type: blockType,
    frame,
    style: { zIndex: 2, color: "#ffffff" },
    dataBinding: {
      operationId,
      params: { ...(options.defaultParams ?? {}) },
      displayMode:
        options.displayMode ??
        (blockType === "data_metric"
          ? "auto"
          : blockType === "data_chart"
            ? "line_chart"
            : blockType === "data_table"
              ? "table"
              : "kpi"),
      label: options.label,
    },
  };
}

export function defaultFrame(type: ComunicadoBlock["type"], shape?: ComunicadoShapeKind): ComunicadoFrame {
  if (type === "data_kpi") return { x: 5, y: 28, w: 28, h: 22 };
  if (type === "data_chart") return { x: 10, y: 28, w: 80, h: 45 };
  if (type === "data_table") return { x: 5, y: 55, w: 90, h: 35 };
  if (type === "data_metric") return { x: 5, y: 28, w: 28, h: 22 };
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
  if (isDataBlockType(type)) {
    return { zIndex: 2, color: "#ffffff" };
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
  if (type === "image" || type === "video") {
    return { ...base, type };
  }
  if (isDataBlockType(type)) {
    return createDataBlock("", { blockType: type });
  }
  return { ...base, type: "text", content };
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
      dataFilters: normalizeDataFilters(cfg.dataFilters),
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
  if (blocks.some((block) => isDataBlockType(block.type))) return 4;
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
      : background.type === "gradient"
        ? {
            type: "gradient",
            from: background.from,
            to: background.to,
            angle: background.angle ?? 180,
          }
        : { type: "color", value: background.value || "#0f172a" };
  const blocks = (config.blocks ?? []).map(serializeBlock);
  const version = config.version ?? detectConfigVersion(config.blocks ?? []);
  const payload: Record<string, unknown> = {
    version,
    headline:
      headingBlock && "content" in headingBlock
        ? headingBlock.content
        : config.headline ?? DEFAULT_HEADLINE,
    subtitle: textBlock && "content" in textBlock ? textBlock.content : config.subtitle ?? "",
    background: serializedBackground,
    blocks,
  };
  if (config.dataFilters && Object.keys(config.dataFilters).length > 0) {
    payload.dataFilters = config.dataFilters;
  }
  return payload;
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
  } else if (isDataBlockType(block.type) && "dataBinding" in block) {
    base.dataBinding = {
      operationId: block.dataBinding.operationId,
      params: block.dataBinding.params ?? {},
      displayMode: block.dataBinding.displayMode,
      label: block.dataBinding.label,
      valueField: block.dataBinding.valueField,
      maxRows: block.dataBinding.maxRows,
      refreshSec: block.dataBinding.refreshSec,
    };
  }
  return base;
}

function normalizeDataFilters(value: unknown): ComunicadoDataFilters | undefined {
  if (!value || typeof value !== "object") return undefined;
  const filters: ComunicadoDataFilters = {};
  for (const [key, raw] of Object.entries(value as Record<string, unknown>)) {
    if (raw === null || raw === undefined || raw === "") continue;
    if (typeof raw === "string" || typeof raw === "number" || typeof raw === "boolean") {
      filters[key] = raw;
    }
  }
  return Object.keys(filters).length > 0 ? filters : undefined;
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
  if (bg.type === "gradient") {
    const from = typeof bg.from === "string" && bg.from.trim() ? bg.from : "#0f172a";
    const to = typeof bg.to === "string" && bg.to.trim() ? bg.to : "#1e3a5f";
    const angle = typeof bg.angle === "number" ? bg.angle : 180;
    return { type: "gradient", from, to, angle };
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
  if (isDataBlockType(type)) {
    const bindingRaw = block.dataBinding;
    const binding =
      bindingRaw && typeof bindingRaw === "object"
        ? (bindingRaw as ComunicadoDataBinding)
        : { operationId: "" };
    return {
      id,
      type,
      frame,
      style: { ...defaultStyle(type), ...style },
      dataBinding: {
        operationId: String(binding.operationId ?? ""),
        params: (binding.params as ComunicadoDataBinding["params"]) ?? {},
        displayMode: binding.displayMode,
        label: binding.label,
        valueField: binding.valueField,
        maxRows: binding.maxRows,
        refreshSec: binding.refreshSec,
      },
      resolved:
        block.resolved && typeof block.resolved === "object"
          ? (block.resolved as ComunicadoDataResolved)
          : undefined,
    } as ComunicadoBlock;
  }
  if (type === "image" || type === "video") {
    return {
      id,
      type,
      frame,
      style,
      assetId: typeof block.assetId === "string" ? block.assetId : undefined,
      url: typeof block.url === "string" ? block.url : undefined,
    };
  }
  return createBlock("text", "");
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
