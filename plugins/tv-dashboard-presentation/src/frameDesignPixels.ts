import type { ComunicadoFrame } from "./comunicadoTypes";
import { resolveViewportPixelSize, type ViewportPixelSize } from "./viewportPixelSize";

/** Lado padrão (px de design) ao inserir forma fechada / seta / balão. */
export const DEFAULT_SHAPE_INSERT_SIZE_PX = 400;
/** Lado padrão (px de design) ao inserir ícone. */
export const DEFAULT_ICON_INSERT_SIZE_PX = 160;
/** Lado padrão (px de design) ao inserir texto. */
export const DEFAULT_TEXT_INSERT_SIZE_PX = 400;
/** Lado padrão (px de design) ao inserir título. */
export const DEFAULT_HEADING_INSERT_SIZE_PX = 480;

/** % do eixo → px de design. */
export function percentToDesignPx(percent: number, axisSize: number): number {
  if (!(axisSize > 0) || !Number.isFinite(percent)) return 0;
  return (percent / 100) * axisSize;
}

/** px de design → % do eixo. */
export function designPxToPercent(px: number, axisSize: number): number {
  if (!(axisSize > 0) || !Number.isFinite(px)) return 0;
  return (px / axisSize) * 100;
}

/**
 * Frame com o mesmo valor de largura e altura em px de design (quadrado visual).
 * No palco 16:9 os % de w/h diferem — a UI (Larg./Alt. px) e o círculo ficam corretos.
 */
export function squareFrameFromDesignPx(
  sizePx: number,
  origin: { x?: number; y?: number } = {},
  designSize: ViewportPixelSize = resolveViewportPixelSize("1080p"),
): ComunicadoFrame {
  const size = Math.max(1, Number.isFinite(sizePx) ? sizePx : 1);
  return {
    x: origin.x ?? 30,
    y: origin.y ?? 30,
    w: designPxToPercent(size, designSize.width),
    h: designPxToPercent(size, designSize.height),
  };
}

/** Frame persistido (%) → px de design do slide/host. */
export function framePercentToDesignPx(
  frame: ComunicadoFrame,
  designSize: ViewportPixelSize,
): ComunicadoFrame {
  return {
    x: percentToDesignPx(frame.x, designSize.width),
    y: percentToDesignPx(frame.y, designSize.height),
    w: percentToDesignPx(frame.w, designSize.width),
    h: percentToDesignPx(frame.h, designSize.height),
  };
}

/** Frame em px de design → % para persistência. */
export function frameDesignPxToPercent(
  framePx: ComunicadoFrame,
  designSize: ViewportPixelSize,
): ComunicadoFrame {
  return {
    x: designPxToPercent(framePx.x, designSize.width),
    y: designPxToPercent(framePx.y, designSize.height),
    w: designPxToPercent(framePx.w, designSize.width),
    h: designPxToPercent(framePx.h, designSize.height),
  };
}

/**
 * Tamanho do host em px de design a partir do frame %-do-slide do bloco
 * (partes KPI/chart usam % relativos a este host).
 */
export function hostDesignSizeFromFramePercent(
  hostFramePct: Pick<ComunicadoFrame, "w" | "h">,
  slideDesign: ViewportPixelSize,
): ViewportPixelSize {
  return {
    width: Math.max(1, percentToDesignPx(hostFramePct.w, slideDesign.width)),
    height: Math.max(1, percentToDesignPx(hostFramePct.h, slideDesign.height)),
  };
}

/**
 * Soft bound de posição (% do slide) — evita valores patológicos; pode ficar fora
 * do retângulo 0–100 (objeto parcialmente ou totalmente fora da tela da TV).
 */
export const FRAME_POSITION_SOFT_MIN = -500;
export const FRAME_POSITION_SOFT_MAX = 500;

/**
 * Único piso de largura/altura do frame (% do palco): maior que zero.
 * Sem teto artificial — o bloco pode ultrapassar o slide.
 */
export const COMUNICADO_FRAME_MIN_SIZE_PCT = 1e-4;

export function clampFramePositionPercent(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.max(FRAME_POSITION_SOFT_MIN, Math.min(FRAME_POSITION_SOFT_MAX, value));
}

/** Normaliza w/h: finito e > 0. Sem máximo. */
export function clampFrameSizePercent(value: number): number {
  if (!Number.isFinite(value)) return COMUNICADO_FRAME_MIN_SIZE_PCT;
  return Math.max(COMUNICADO_FRAME_MIN_SIZE_PCT, value);
}

/** Ajusta eixo do frame: tamanho só > 0; posição livre (fora do slide permitido). */
export function patchComunicadoFrame(
  frame: ComunicadoFrame,
  key: keyof ComunicadoFrame,
  raw: number,
): ComunicadoFrame {
  const value = Number.isFinite(raw) ? raw : frame[key];
  if (key === "w" || key === "h") {
    return { ...frame, [key]: clampFrameSizePercent(value) };
  }
  return { ...frame, [key]: clampFramePositionPercent(value) };
}

/**
 * Edita um eixo em px de design e devolve frame em % (persistência).
 * `designSize` = slide (bloco) ou host (parte KPI/chart).
 */
export function patchComunicadoFrameDesignPx(
  framePct: ComunicadoFrame,
  key: keyof ComunicadoFrame,
  rawPx: number,
  designSize: ViewportPixelSize,
): ComunicadoFrame {
  const axis = key === "x" || key === "w" ? designSize.width : designSize.height;
  const pct = designPxToPercent(rawPx, axis);
  return patchComunicadoFrame(framePct, key, pct);
}

/** Valor exibido na UI (px de design, 1 casa quando necessário). */
export function formatDesignPx(value: number): number {
  if (!Number.isFinite(value)) return 0;
  const rounded = Math.round(value * 10) / 10;
  return Number.isInteger(rounded) ? rounded : rounded;
}
