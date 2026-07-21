import type { ComunicadoBlock, ComunicadoFrame } from "@delpi/tv-dashboard-presentation";

import {
  partitionSelectionIntoLayoutUnits,
  type ComunicadoLayoutUnit,
} from "./comunicadoGrouping";

export type LayoutAlignCommand =
  | "align-left"
  | "align-center-h"
  | "align-right"
  | "align-top"
  | "align-center-v"
  | "align-bottom"
  | "distribute-h"
  | "distribute-v";

function applyUnitOrigins(
  blocks: ComunicadoBlock[],
  units: ComunicadoLayoutUnit[],
  nextOrigins: Map<string, { x: number; y: number }>,
): ComunicadoBlock[] {
  const frameById = new Map<string, ComunicadoFrame>();
  for (const unit of units) {
    const next = nextOrigins.get(unit.key);
    if (!next) continue;
    const dx = next.x - unit.frame.x;
    const dy = next.y - unit.frame.y;
    if (dx === 0 && dy === 0) continue;
    for (const memberId of unit.memberIds) {
      const block = blocks.find((item) => item.id === memberId);
      if (!block) continue;
      frameById.set(memberId, {
        ...block.frame,
        x: block.frame.x + dx,
        y: block.frame.y + dy,
      });
    }
  }
  if (frameById.size === 0) return blocks;
  return blocks.map((block) => {
    const frame = frameById.get(block.id);
    return frame ? { ...block, frame } : block;
  });
}

function computeUnitOrigins(
  units: ComunicadoLayoutUnit[],
  command: LayoutAlignCommand,
): Map<string, { x: number; y: number }> | null {
  const origins = new Map<string, { x: number; y: number }>();

  switch (command) {
    case "align-left": {
      const minX = Math.min(...units.map((unit) => unit.frame.x));
      for (const unit of units) origins.set(unit.key, { x: minX, y: unit.frame.y });
      return origins;
    }
    case "align-right": {
      const maxRight = Math.max(...units.map((unit) => unit.frame.x + unit.frame.w));
      for (const unit of units) {
        origins.set(unit.key, { x: maxRight - unit.frame.w, y: unit.frame.y });
      }
      return origins;
    }
    case "align-center-h": {
      const minX = Math.min(...units.map((unit) => unit.frame.x));
      const maxRight = Math.max(...units.map((unit) => unit.frame.x + unit.frame.w));
      const center = (minX + maxRight) / 2;
      for (const unit of units) {
        origins.set(unit.key, { x: center - unit.frame.w / 2, y: unit.frame.y });
      }
      return origins;
    }
    case "align-top": {
      const minY = Math.min(...units.map((unit) => unit.frame.y));
      for (const unit of units) origins.set(unit.key, { x: unit.frame.x, y: minY });
      return origins;
    }
    case "align-bottom": {
      const maxBottom = Math.max(...units.map((unit) => unit.frame.y + unit.frame.h));
      for (const unit of units) {
        origins.set(unit.key, { x: unit.frame.x, y: maxBottom - unit.frame.h });
      }
      return origins;
    }
    case "align-center-v": {
      const minY = Math.min(...units.map((unit) => unit.frame.y));
      const maxBottom = Math.max(...units.map((unit) => unit.frame.y + unit.frame.h));
      const center = (minY + maxBottom) / 2;
      for (const unit of units) {
        origins.set(unit.key, { x: unit.frame.x, y: center - unit.frame.h / 2 });
      }
      return origins;
    }
    case "distribute-h": {
      const sorted = [...units].sort((a, b) => a.frame.x - b.frame.x);
      const first = sorted[0];
      const last = sorted[sorted.length - 1];
      const span = last.frame.x + last.frame.w - first.frame.x;
      const totalWidth = sorted.reduce((sum, unit) => sum + unit.frame.w, 0);
      const gap = (span - totalWidth) / (sorted.length - 1);
      let cursor = first.frame.x;
      for (const unit of sorted) {
        origins.set(unit.key, { x: cursor, y: unit.frame.y });
        cursor += unit.frame.w + gap;
      }
      return origins;
    }
    case "distribute-v": {
      const sorted = [...units].sort((a, b) => a.frame.y - b.frame.y);
      const first = sorted[0];
      const last = sorted[sorted.length - 1];
      const span = last.frame.y + last.frame.h - first.frame.y;
      const totalHeight = sorted.reduce((sum, unit) => sum + unit.frame.h, 0);
      const gap = (span - totalHeight) / (sorted.length - 1);
      let cursor = first.frame.y;
      for (const unit of sorted) {
        origins.set(unit.key, { x: unit.frame.x, y: cursor });
        cursor += unit.frame.h + gap;
      }
      return origins;
    }
    default:
      return null;
  }
}

/**
 * Alinha/distribui a seleção por **unidades de layout** (grupos fechados ou blocos).
 * Membros de um grupo recebem o mesmo delta — layout interno preservado.
 */
export function alignComunicadoBlocks(
  blocks: ComunicadoBlock[],
  selectedIds: string[],
  command: LayoutAlignCommand,
): ComunicadoBlock[] {
  const units = partitionSelectionIntoLayoutUnits(blocks, selectedIds);
  if (units.length === 0) return blocks;

  if (command === "distribute-h" || command === "distribute-v") {
    if (units.length < 3) return blocks;
  } else if (units.length < 2) {
    return blocks;
  }

  const origins = computeUnitOrigins(units, command);
  if (!origins) return blocks;
  return applyUnitOrigins(blocks, units, origins);
}
