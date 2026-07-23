import type { ComunicadoFrame } from "@delpi/tv-dashboard-presentation";

import { unionFramePercent } from "./comunicadoGrouping";

export type ClientRectLike = {
  left: number;
  top: number;
  width: number;
  height: number;
};

/**
 * Âncora do menu de contexto (Shift+F10 / tecla Menu) em coords de cliente.
 * Com frames: canto inferior direito do bbox unificado (padrão Office).
 * Sem frames: centro do canvas.
 */
export function resolveStageContextMenuAnchorClient(input: {
  canvasRect: ClientRectLike;
  frames: ComunicadoFrame[];
}): { x: number; y: number } {
  const { canvasRect, frames } = input;
  const { left, top, width, height } = canvasRect;
  if (!(width > 0) || !(height > 0)) {
    return { x: left, y: top };
  }

  if (frames.length === 0) {
    return {
      x: left + width / 2,
      y: top + height / 2,
    };
  }

  const union = unionFramePercent(frames);
  return {
    x: left + ((union.x + union.w) / 100) * width,
    y: top + ((union.y + union.h) / 100) * height,
  };
}
