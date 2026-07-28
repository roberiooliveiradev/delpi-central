import type { ComunicadoFrame } from "./comunicadoTypes";
import {
  designPxToPercent,
  frameDesignPxToPercent,
  framePercentToDesignPx,
} from "./frameDesignPixels";
import { resolveViewportPixelSize, type ViewportPixelSize } from "./viewportPixelSize";

/** Fator médio glifo/em (Inter / system UI) — paridade com tipografia do deck. */
export const TEXT_CHAR_WIDTH_FACTOR = 0.56;

export const TEXT_BOX_HUG_MIN_WIDTH_PX = 48;
export const TEXT_BOX_HUG_MIN_HEIGHT_PX = 32;

/** Largura máxima ao abraçar texto na inserção (quebra linha além disso). */
export const DEFAULT_TEXT_INSERT_MAX_WIDTH_PX = 520;

/** Padding tipográfico (espelha `VISUAL_BOX_CONTENT_INSET` = 6px). */
export const TEXT_BOX_HUG_INSET_PX = 6;

export type VisualBoxHugAxes = {
  width: boolean;
  height: boolean;
};

/** Handle de resize do chrome (`nw`…`se`) — define qual borda permanece fixa. */
export type VisualBoxResizeHandlePosition =
  | "nw"
  | "n"
  | "ne"
  | "w"
  | "e"
  | "sw"
  | "s"
  | "se";

/**
 * Estima bbox do texto em px de design (sem DOM) — inserção de text/heading.
 * Espelha o espírito Figma «Hug contents» / caixa PPT auto-altura.
 */
export function estimateTextContentSizePx(options: {
  content: string;
  fontSize: number;
  lineHeight?: number;
  paddingPx?: number;
  maxWidthPx?: number;
}): { w: number; h: number } {
  const fontSize = Math.max(8, options.fontSize || 28);
  const lineHeight = options.lineHeight && options.lineHeight > 0 ? options.lineHeight : 1.15;
  const pad = (options.paddingPx ?? TEXT_BOX_HUG_INSET_PX) * 2;
  const raw = options.content.length > 0 ? options.content : " ";
  const lines = raw.split(/\r?\n/);
  const charW = fontSize * TEXT_CHAR_WIDTH_FACTOR;
  const maxWidth = options.maxWidthPx;

  let contentW = 0;
  let totalLines = 0;
  for (const line of lines) {
    const len = Math.max(1, Array.from(line).length);
    const natural = len * charW;
    if (maxWidth != null && maxWidth > pad) {
      const inner = Math.max(charW, maxWidth - pad);
      const wrapped = Math.max(1, Math.ceil(natural / inner));
      contentW = Math.max(contentW, Math.min(natural, inner));
      totalLines += wrapped;
    } else {
      contentW = Math.max(contentW, natural);
      totalLines += 1;
    }
  }

  const w = Math.max(TEXT_BOX_HUG_MIN_WIDTH_PX, Math.ceil(contentW + pad));
  const h = Math.max(
    TEXT_BOX_HUG_MIN_HEIGHT_PX,
    Math.ceil(totalLines * fontSize * lineHeight + pad),
  );
  return { w, h };
}

/** Frame %-do-slide a partir do conteúdo (inserção text/heading). */
export function textBoxFrameFromContent(options: {
  content: string;
  fontSize: number;
  lineHeight?: number;
  origin?: { x?: number; y?: number };
  designSize?: ViewportPixelSize;
  maxWidthPx?: number;
}): ComunicadoFrame {
  const design = options.designSize ?? resolveViewportPixelSize("1080p");
  const size = estimateTextContentSizePx({
    content: options.content,
    fontSize: options.fontSize,
    lineHeight: options.lineHeight,
    maxWidthPx: options.maxWidthPx ?? DEFAULT_TEXT_INSERT_MAX_WIDTH_PX,
  });
  return {
    x: options.origin?.x ?? 5,
    y: options.origin?.y ?? 34,
    w: designPxToPercent(size.w, design.width),
    h: designPxToPercent(size.h, design.height),
  };
}

/**
 * Figma: duplo clique na borda vertical → hug width; horizontal → hug height;
 * canto → ambos.
 */
export function resizeHandleToHugAxes(
  position: VisualBoxResizeHandlePosition,
): VisualBoxHugAxes {
  if (position === "e" || position === "w") return { width: true, height: false };
  if (position === "n" || position === "s") return { width: false, height: true };
  return { width: true, height: true };
}

export function resizeModeToHandlePosition(
  mode: string,
): VisualBoxResizeHandlePosition | null {
  const match = /^resize-(nw|n|ne|w|e|sw|s|se)$/.exec(mode);
  return match ? (match[1] as VisualBoxResizeHandlePosition) : null;
}

/**
 * Ajusta o frame ao tamanho medido do texto, mantendo a borda oposta ao handle
 * (mesmo contrato Figma hug na edge).
 */
export function hugFrameToContentSizePx(
  frame: ComunicadoFrame,
  contentPx: { w: number; h: number },
  designSize: ViewportPixelSize,
  axes: VisualBoxHugAxes,
  handle: VisualBoxResizeHandlePosition,
): ComunicadoFrame {
  const px = framePercentToDesignPx(frame, designSize);
  let { x, y, w, h } = px;
  const nextW = Math.max(
    TEXT_BOX_HUG_MIN_WIDTH_PX,
    Number.isFinite(contentPx.w) ? contentPx.w : w,
  );
  const nextH = Math.max(
    TEXT_BOX_HUG_MIN_HEIGHT_PX,
    Number.isFinite(contentPx.h) ? contentPx.h : h,
  );

  if (axes.width) {
    const keepRight = handle === "w" || handle === "nw" || handle === "sw";
    if (keepRight) x = x + w - nextW;
    w = nextW;
  }
  if (axes.height) {
    const keepBottom = handle === "n" || handle === "nw" || handle === "ne";
    if (keepBottom) y = y + h - nextH;
    h = nextH;
  }

  return frameDesignPxToPercent({ x, y, w, h }, designSize);
}
