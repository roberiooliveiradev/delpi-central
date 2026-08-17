import {
  isLineShapeKind,
  type ComunicadoBlock,
  type ComunicadoFrame,
} from "@delpi/tv-dashboard-presentation";

import { partitionSelectionIntoLayoutUnits } from "./comunicadoGrouping";

export type SameSizeAxis = "width" | "height" | "both";

/** Linhas não entram em Mesmo tamanho (só bbox, sem sentido de L/A). */
export function isSameSizeResizableBlock(block: ComunicadoBlock): boolean {
  return !(block.type === "shape" && isLineShapeKind(block.shape));
}

/** Referência = último id selecionado que aceita resize (invariante E5). */
export function resolveSameSizePrimaryId(
  blocks: readonly ComunicadoBlock[],
  selectedIds: readonly string[],
): string | null {
  for (let index = selectedIds.length - 1; index >= 0; index -= 1) {
    const id = selectedIds[index];
    if (!id) continue;
    const block = blocks.find((item) => item.id === id);
    if (block && isSameSizeResizableBlock(block)) return id;
  }
  return null;
}

export function countSameSizeTargets(
  blocks: ComunicadoBlock[],
  selectedIds: readonly string[],
): number {
  const units = partitionSelectionIntoLayoutUnits(blocks, [...selectedIds], {
    expandClosedGroups: true,
  });
  return units.filter((unit) => {
    const memberId = unit.memberIds[0];
    const block = memberId ? blocks.find((item) => item.id === memberId) : undefined;
    return Boolean(block && isSameSizeResizableBlock(block));
  }).length;
}

export function canApplySameSize(
  blocks: ComunicadoBlock[],
  selectedIds: readonly string[],
): boolean {
  return countSameSizeTargets(blocks, selectedIds) >= 2;
}

/**
 * Copia L / A / ambos do primário para os demais membros.
 * Não altera x/y. Grupo fechado = uma unidade por membro.
 */
export function resizeComunicadoBlocksSameSize(
  blocks: ComunicadoBlock[],
  selectedIds: string[],
  axis: SameSizeAxis,
): ComunicadoBlock[] {
  const primaryId = resolveSameSizePrimaryId(blocks, selectedIds);
  if (!primaryId) return blocks;
  const primary = blocks.find((block) => block.id === primaryId);
  if (!primary) return blocks;

  const units = partitionSelectionIntoLayoutUnits(blocks, selectedIds, {
    expandClosedGroups: true,
  });
  if (units.length < 2) return blocks;

  const applyW = axis === "width" || axis === "both";
  const applyH = axis === "height" || axis === "both";
  const frameById = new Map<string, ComunicadoFrame>();

  for (const unit of units) {
    for (const memberId of unit.memberIds) {
      if (memberId === primaryId) continue;
      const block = blocks.find((item) => item.id === memberId);
      if (!block || !isSameSizeResizableBlock(block)) continue;
      frameById.set(memberId, {
        ...block.frame,
        w: applyW ? primary.frame.w : block.frame.w,
        h: applyH ? primary.frame.h : block.frame.h,
      });
    }
  }

  if (frameById.size === 0) return blocks;
  return blocks.map((block) => {
    const frame = frameById.get(block.id);
    return frame ? { ...block, frame } : block;
  });
}
