import type { ComunicadoFrame } from "@delpi/tv-dashboard-presentation";

/** Centro da viewport (wrap) em % do slide (canvas). */
export function resolveViewportCenterCanvasPercent(
  canvas: HTMLElement | null | undefined,
  wrap?: HTMLElement | null | undefined,
): { x: number; y: number } | null {
  if (!canvas) return null;
  const canvasRect = canvas.getBoundingClientRect();
  if (!(canvasRect.width > 0) || !(canvasRect.height > 0)) return null;

  let clientX = canvasRect.left + canvasRect.width / 2;
  let clientY = canvasRect.top + canvasRect.height / 2;
  if (wrap) {
    const wrapRect = wrap.getBoundingClientRect();
    if (wrapRect.width > 0 && wrapRect.height > 0) {
      clientX = wrapRect.left + wrapRect.width / 2;
      clientY = wrapRect.top + wrapRect.height / 2;
    }
  }

  return {
    x: ((clientX - canvasRect.left) / canvasRect.width) * 100,
    y: ((clientY - canvasRect.top) / canvasRect.height) * 100,
  };
}

/**
 * Reposiciona o frame para que o centro do bloco coincida com `center`
 * (coords % do slide), mantendo w/h e clampeando no slide.
 */
export function placeFrameCenteredAt(
  frame: ComunicadoFrame,
  center: { x: number; y: number },
): ComunicadoFrame {
  const w = Number.isFinite(frame.w) ? Math.max(0, frame.w) : 0;
  const h = Number.isFinite(frame.h) ? Math.max(0, frame.h) : 0;
  const maxX = Math.max(0, 100 - w);
  const maxY = Math.max(0, 100 - h);
  const x = Math.min(maxX, Math.max(0, center.x - w / 2));
  const y = Math.min(maxY, Math.max(0, center.y - h / 2));
  return { ...frame, x, y, w, h };
}

/** Aplica centro da viewport ao frame; sem DOM válido, devolve o frame original. */
export function placeFrameInViewportCenter(
  frame: ComunicadoFrame,
  canvas: HTMLElement | null | undefined,
  wrap?: HTMLElement | null | undefined,
): ComunicadoFrame {
  const center = resolveViewportCenterCanvasPercent(canvas, wrap);
  if (!center) return frame;
  return placeFrameCenteredAt(frame, center);
}

/** Reposiciona o frame do bloco no centro da viewport do editor. */
export function placeBlockInViewportCenter<T extends { frame: ComunicadoFrame }>(
  block: T,
  canvas: HTMLElement | null | undefined,
  wrap?: HTMLElement | null | undefined,
): T {
  return { ...block, frame: placeFrameInViewportCenter(block.frame, canvas, wrap) };
}
