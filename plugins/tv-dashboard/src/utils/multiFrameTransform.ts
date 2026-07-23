import {
  COMUNICADO_FRAME_MIN_SIZE_PCT,
  type ComunicadoFrame,
} from "@delpi/tv-dashboard-presentation";

import { clampRotationDeg } from "./comunicadoTransform";
import { unionFramePercent } from "./comunicadoGrouping";

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
      w: Math.max(COMUNICADO_FRAME_MIN_SIZE_PCT, start.w + dw),
      h: Math.max(COMUNICADO_FRAME_MIN_SIZE_PCT, start.h + dh),
    });
  }
  return next;
}

export type GroupRotateMemberUpdate = {
  frame: ComunicadoFrame;
  rotation: number;
};

/** Centro do bbox unificado dos frames (coords % do slide). */
export function resolveFramesGroupCenter(
  frames: Iterable<ComunicadoFrame>,
): { x: number; y: number } {
  const list = [...frames];
  const union = unionFramePercent(list);
  return { x: union.x + union.w / 2, y: union.y + union.h / 2 };
}

function rotatePointAround(
  point: { x: number; y: number },
  center: { x: number; y: number },
  deltaDeg: number,
): { x: number; y: number } {
  const rad = (deltaDeg * Math.PI) / 180;
  const cos = Math.cos(rad);
  const sin = Math.sin(rad);
  const dx = point.x - center.x;
  const dy = point.y - center.y;
  return {
    x: center.x + dx * cos - dy * sin,
    y: center.y + dx * sin + dy * cos,
  };
}

/**
 * Gira membros em torno do centro do grupo (frame orbita + style.rotation).
 * Paridade PowerPoint/Figma no handle de giro do chrome do grupo.
 */
export function applyGroupRotationDelta(input: {
  startFrames: ReadonlyMap<string, ComunicadoFrame>;
  startRotations: ReadonlyMap<string, number>;
  center: { x: number; y: number };
  deltaDeg: number;
}): Map<string, GroupRotateMemberUpdate> {
  const next = new Map<string, GroupRotateMemberUpdate>();
  for (const [id, start] of input.startFrames) {
    const cx = start.x + start.w / 2;
    const cy = start.y + start.h / 2;
    const rotated = rotatePointAround({ x: cx, y: cy }, input.center, input.deltaDeg);
    const startRotation = input.startRotations.get(id) ?? 0;
    next.set(id, {
      frame: {
        x: rotated.x - start.w / 2,
        y: rotated.y - start.h / 2,
        w: start.w,
        h: start.h,
      },
      rotation: clampRotationDeg(startRotation + input.deltaDeg),
    });
  }
  return next;
}
