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

export function normalizeMarqueeRect(rect: MarqueeRect): MarqueeRect {
  return {
    x1: Math.min(rect.x1, rect.x2),
    y1: Math.min(rect.y1, rect.y2),
    x2: Math.max(rect.x1, rect.x2),
    y2: Math.max(rect.y1, rect.y2),
  };
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
