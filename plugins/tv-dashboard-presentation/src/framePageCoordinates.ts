import type { ComunicadoFrame } from "./comunicadoTypes";
import {
  frameDesignPxToPercent,
  framePercentToDesignPx,
  hostDesignSizeFromFramePercent,
  patchComunicadoFrame,
  percentToDesignPx,
} from "./frameDesignPixels";
import type { ViewportPixelSize } from "./viewportPixelSize";

/**
 * UI e réguas usam origem no canto inferior esquerdo da página.
 * Persistência CSS permanece top-left em % do slide (ou % do host nas partes).
 */

/** Y do canto inferior do box, medido desde a base da página (px de design). */
export function designYTopLeftToBottomLeft(
  yTop: number,
  pageHeight: number,
  boxHeight: number,
): number {
  if (!(pageHeight > 0) || !Number.isFinite(yTop) || !Number.isFinite(boxHeight)) return 0;
  return pageHeight - yTop - boxHeight;
}

/** Y top-left (modelo CSS) a partir do Y bottom-left da UI. */
export function designYBottomLeftToTopLeft(
  yBottom: number,
  pageHeight: number,
  boxHeight: number,
): number {
  if (!(pageHeight > 0) || !Number.isFinite(yBottom) || !Number.isFinite(boxHeight)) return 0;
  return pageHeight - yBottom - boxHeight;
}

/** Normaliza tamanho e posição (posição pode ficar fora do slide). */
function clampFramePercent(pct: ComunicadoFrame): ComunicadoFrame {
  let next: ComunicadoFrame = { x: 0, y: 0, w: 0.5, h: 0.5 };
  next = patchComunicadoFrame(next, "w", pct.w);
  next = patchComunicadoFrame(next, "h", pct.h);
  next = patchComunicadoFrame(next, "x", pct.x);
  next = patchComunicadoFrame(next, "y", pct.y);
  return next;
}

/**
 * Frame %-do-slide → px de design na página, Y desde o canto inferior esquerdo
 * (âncora = canto inferior esquerdo do elemento).
 */
export function framePercentToPageBottomLeftPx(
  frame: ComunicadoFrame,
  slideDesign: ViewportPixelSize,
): ComunicadoFrame {
  const topLeft = framePercentToDesignPx(frame, slideDesign);
  return {
    x: topLeft.x,
    y: designYTopLeftToBottomLeft(topLeft.y, slideDesign.height, topLeft.h),
    w: topLeft.w,
    h: topLeft.h,
  };
}

/**
 * Edita um eixo em px de página (origem inferior esquerda) e devolve % do slide.
 * Ao mudar a altura, a base do elemento permanece fixa.
 */
export function patchComunicadoFramePageBottomLeftPx(
  framePct: ComunicadoFrame,
  key: keyof ComunicadoFrame,
  rawPx: number,
  slideDesign: ViewportPixelSize,
): ComunicadoFrame {
  const page = framePercentToPageBottomLeftPx(framePct, slideDesign);
  const value = Number.isFinite(rawPx) ? rawPx : page[key];
  const nextPage: ComunicadoFrame = { ...page, [key]: value };

  const topLeft: ComunicadoFrame = {
    x: nextPage.x,
    y: designYBottomLeftToTopLeft(nextPage.y, slideDesign.height, nextPage.h),
    w: nextPage.w,
    h: nextPage.h,
  };
  return clampFramePercent(frameDesignPxToPercent(topLeft, slideDesign));
}

/**
 * Parte (% do host) → px absolutos da página, Y desde o canto inferior esquerdo.
 */
export function hostRelativeFrameToPageBottomLeftPx(
  partFrame: ComunicadoFrame,
  hostFramePct: ComunicadoFrame,
  slideDesign: ViewportPixelSize,
): ComunicadoFrame {
  const hostTopLeft = framePercentToDesignPx(hostFramePct, slideDesign);
  const hostSize = hostDesignSizeFromFramePercent(hostFramePct, slideDesign);
  const local = framePercentToDesignPx(partFrame, hostSize);
  const absTopLeft: ComunicadoFrame = {
    x: hostTopLeft.x + local.x,
    y: hostTopLeft.y + local.y,
    w: local.w,
    h: local.h,
  };
  return {
    x: absTopLeft.x,
    y: designYTopLeftToBottomLeft(absTopLeft.y, slideDesign.height, absTopLeft.h),
    w: absTopLeft.w,
    h: absTopLeft.h,
  };
}

/**
 * Edita parte em px de página (origem inferior esquerda) → % relativos ao host.
 * A base do elemento permanece fixa ao mudar a altura.
 */
export function patchHostRelativeFramePageBottomLeftPx(
  partFrame: ComunicadoFrame,
  hostFramePct: ComunicadoFrame,
  key: keyof ComunicadoFrame,
  rawPx: number,
  slideDesign: ViewportPixelSize,
): ComunicadoFrame {
  const page = hostRelativeFrameToPageBottomLeftPx(partFrame, hostFramePct, slideDesign);
  const value = Number.isFinite(rawPx) ? rawPx : page[key];
  const nextPage: ComunicadoFrame = { ...page, [key]: value };

  const absTopLeft: ComunicadoFrame = {
    x: nextPage.x,
    y: designYBottomLeftToTopLeft(nextPage.y, slideDesign.height, nextPage.h),
    w: nextPage.w,
    h: nextPage.h,
  };

  const hostTopLeft = framePercentToDesignPx(hostFramePct, slideDesign);
  const hostSize = hostDesignSizeFromFramePercent(hostFramePct, slideDesign);
  const localTopLeft: ComunicadoFrame = {
    x: absTopLeft.x - hostTopLeft.x,
    y: absTopLeft.y - hostTopLeft.y,
    w: absTopLeft.w,
    h: absTopLeft.h,
  };

  return clampFramePercent(frameDesignPxToPercent(localTopLeft, hostSize));
}

/** Host frame em % do slide → canto inferior esquerdo em px de página (só leitura). */
export function hostFramePageBottomLeftOrigin(
  hostFramePct: ComunicadoFrame,
  slideDesign: ViewportPixelSize,
): { x: number; y: number } {
  const hostTopLeft = framePercentToDesignPx(hostFramePct, slideDesign);
  const hostH = percentToDesignPx(hostFramePct.h, slideDesign.height);
  return {
    x: hostTopLeft.x,
    y: designYTopLeftToBottomLeft(hostTopLeft.y, slideDesign.height, hostH),
  };
}
