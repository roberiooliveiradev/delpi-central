import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

export type LayoutAlignCommand =
  | "align-left"
  | "align-center-h"
  | "align-right"
  | "align-top"
  | "align-center-v"
  | "align-bottom"
  | "distribute-h"
  | "distribute-v";

function selectedBlocks(blocks: ComunicadoBlock[], selectedIds: string[]): ComunicadoBlock[] {
  const idSet = new Set(selectedIds);
  return blocks.filter((block) => idSet.has(block.id));
}

export function alignComunicadoBlocks(
  blocks: ComunicadoBlock[],
  selectedIds: string[],
  command: LayoutAlignCommand,
): ComunicadoBlock[] {
  const selected = selectedBlocks(blocks, selectedIds);
  if (selected.length === 0) return blocks;
  const idSet = new Set(selectedIds);

  if (command === "distribute-h" || command === "distribute-v") {
    if (selected.length < 3) return blocks;
  } else if (selected.length < 2) {
    return blocks;
  }

  const patchFrame = (blockId: string, frame: ComunicadoBlock["frame"]) =>
    blocks.map((block) => (block.id === blockId ? { ...block, frame } : block));

  switch (command) {
    case "align-left": {
      const minX = Math.min(...selected.map((block) => block.frame.x));
      return blocks.map((block) =>
        idSet.has(block.id) ? { ...block, frame: { ...block.frame, x: minX } } : block,
      );
    }
    case "align-right": {
      const maxRight = Math.max(...selected.map((block) => block.frame.x + block.frame.w));
      return blocks.map((block) =>
        idSet.has(block.id)
          ? { ...block, frame: { ...block.frame, x: maxRight - block.frame.w } }
          : block,
      );
    }
    case "align-center-h": {
      const minX = Math.min(...selected.map((block) => block.frame.x));
      const maxRight = Math.max(...selected.map((block) => block.frame.x + block.frame.w));
      const center = (minX + maxRight) / 2;
      return blocks.map((block) =>
        idSet.has(block.id)
          ? { ...block, frame: { ...block.frame, x: center - block.frame.w / 2 } }
          : block,
      );
    }
    case "align-top": {
      const minY = Math.min(...selected.map((block) => block.frame.y));
      return blocks.map((block) =>
        idSet.has(block.id) ? { ...block, frame: { ...block.frame, y: minY } } : block,
      );
    }
    case "align-bottom": {
      const maxBottom = Math.max(...selected.map((block) => block.frame.y + block.frame.h));
      return blocks.map((block) =>
        idSet.has(block.id)
          ? { ...block, frame: { ...block.frame, y: maxBottom - block.frame.h } }
          : block,
      );
    }
    case "align-center-v": {
      const minY = Math.min(...selected.map((block) => block.frame.y));
      const maxBottom = Math.max(...selected.map((block) => block.frame.y + block.frame.h));
      const center = (minY + maxBottom) / 2;
      return blocks.map((block) =>
        idSet.has(block.id)
          ? { ...block, frame: { ...block.frame, y: center - block.frame.h / 2 } }
          : block,
      );
    }
    case "distribute-h": {
      const sorted = [...selected].sort((a, b) => a.frame.x - b.frame.x);
      const first = sorted[0];
      const last = sorted[sorted.length - 1];
      const span = last.frame.x + last.frame.w - first.frame.x;
      const totalWidth = sorted.reduce((sum, block) => sum + block.frame.w, 0);
      const gap = (span - totalWidth) / (sorted.length - 1);
      let cursor = first.frame.x;
      const positions = new Map<string, number>();
      for (const block of sorted) {
        positions.set(block.id, cursor);
        cursor += block.frame.w + gap;
      }
      return blocks.map((block) =>
        positions.has(block.id)
          ? { ...block, frame: { ...block.frame, x: positions.get(block.id)! } }
          : block,
      );
    }
    case "distribute-v": {
      const sorted = [...selected].sort((a, b) => a.frame.y - b.frame.y);
      const first = sorted[0];
      const last = sorted[sorted.length - 1];
      const span = last.frame.y + last.frame.h - first.frame.y;
      const totalHeight = sorted.reduce((sum, block) => sum + block.frame.h, 0);
      const gap = (span - totalHeight) / (sorted.length - 1);
      let cursor = first.frame.y;
      const positions = new Map<string, number>();
      for (const block of sorted) {
        positions.set(block.id, cursor);
        cursor += block.frame.h + gap;
      }
      return blocks.map((block) =>
        positions.has(block.id)
          ? { ...block, frame: { ...block.frame, y: positions.get(block.id)! } }
          : block,
      );
    }
    default:
      return blocks;
  }
}
