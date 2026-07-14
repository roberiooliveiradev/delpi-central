import type { ComunicadoFrame } from "@delpi/tv-dashboard-presentation";

/**
 * Aplica o mesmo delta do frame “primary” (arrastado) a cada frame inicial da multi-seleção.
 * Move e resize sobem/descem juntos com dx/dy/dw/dh.
 */
export function applyMultiFrameDelta(
  startFrames: ReadonlyMap<string, ComunicadoFrame>,
  primaryId: string,
  primaryNext: ComunicadoFrame,
): Map<string, ComunicadoFrame> {
  const origin = startFrames.get(primaryId);
  const next = new Map<string, ComunicadoFrame>();
  if (!origin) {
    for (const [id, frame] of startFrames) {
      next.set(id, id === primaryId ? { ...primaryNext } : { ...frame });
    }
    return next;
  }

  const dx = primaryNext.x - origin.x;
  const dy = primaryNext.y - origin.y;
  const dw = primaryNext.w - origin.w;
  const dh = primaryNext.h - origin.h;

  for (const [id, start] of startFrames) {
    if (id === primaryId) {
      next.set(id, { ...primaryNext });
      continue;
    }
    next.set(id, {
      x: start.x + dx,
      y: start.y + dy,
      w: Math.max(0.5, start.w + dw),
      h: Math.max(0.5, start.h + dh),
    });
  }
  return next;
}
