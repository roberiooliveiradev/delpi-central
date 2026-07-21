import type { ComunicadoBlock, ComunicadoFrame } from "@delpi/tv-dashboard-presentation";
import {
  isBlockSelectableOnStage,
  resolveBlockHitFrame,
} from "@delpi/tv-dashboard-presentation";

export type MarqueeRect = {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
};

/** Esquerda→direita seleciona; direita→esquerda remove da seleção. */
export type MarqueeIntent = "add" | "subtract";

export function normalizeMarqueeRect(rect: MarqueeRect): MarqueeRect {
  return {
    x1: Math.min(rect.x1, rect.x2),
    y1: Math.min(rect.y1, rect.y2),
    x2: Math.max(rect.x1, rect.x2),
    y2: Math.max(rect.y1, rect.y2),
  };
}

/**
 * Direção horizontal do arraste (antes de normalizar).
 * Empate (só vertical) conta como seleção (add).
 */
export function resolveMarqueeIntent(rect: MarqueeRect): MarqueeIntent {
  return rect.x2 < rect.x1 ? "subtract" : "add";
}

function frameIntersectsMarquee(frame: ComunicadoFrame, rect: MarqueeRect): boolean {
  const left = frame.x;
  const top = frame.y;
  const right = frame.x + frame.w;
  const bottom = frame.y + frame.h;
  return left < rect.x2 && right > rect.x1 && top < rect.y2 && bottom > rect.y1;
}

export function blocksInMarquee(blocks: ComunicadoBlock[], rect: MarqueeRect): string[] {
  const normalized = normalizeMarqueeRect(rect);
  return blocks
    .filter(
      (block) =>
        isBlockSelectableOnStage(block, blocks) &&
        frameIntersectsMarquee(resolveBlockHitFrame(block), normalized),
    )
    .map((b) => b.id);
}

/** Une ids à seleção atual (marquee L→R + Shift). */
export function mergeMarqueeSelection(currentIds: string[], hitIds: string[]): string[] {
  return [...new Set([...currentIds, ...hitIds])];
}

/** Remove hits da seleção atual (marquee R→L). */
export function subtractMarqueeSelection(currentIds: string[], hitIds: string[]): string[] {
  if (hitIds.length === 0) return currentIds;
  const remove = new Set(hitIds);
  return currentIds.filter((id) => !remove.has(id));
}
