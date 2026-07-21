import {
  filterStageSelectableIds,
  newBlockId,
  type ComunicadoBlock,
  type ComunicadoFrame,
} from "@delpi/tv-dashboard-presentation";

export function newComunicadoGroupId(): string {
  return `grp_${newBlockId()}`;
}

export function membersOfGroup(
  blocks: ComunicadoBlock[],
  groupId: string | undefined | null,
): ComunicadoBlock[] {
  if (!groupId) return [];
  return blocks.filter((block) => block.groupId === groupId);
}

export function expandSelectionWithGroups(
  blocks: ComunicadoBlock[],
  selectedIds: string[],
): string[] {
  const expanded = new Set(selectedIds);
  for (const id of selectedIds) {
    const block = blocks.find((item) => item.id === id);
    if (!block?.groupId) continue;
    for (const member of blocks) {
      if (member.groupId === block.groupId) expanded.add(member.id);
    }
  }
  return filterStageSelectableIds([...expanded], blocks);
}

/**
 * Seleção «pai»: todos os membros de um único groupId estão selecionados
 * (equivalente à moldura de KPI/gráfico — um chrome externo).
 */
export function resolveClosedGroupSelection(
  blocks: ComunicadoBlock[],
  selectedIds: string[],
): { groupId: string; memberIds: string[]; members: ComunicadoBlock[] } | null {
  if (selectedIds.length < 2) return null;
  const selected = blocks.filter((block) => selectedIds.includes(block.id));
  if (selected.length !== selectedIds.length) return null;
  const groupId = selected[0]?.groupId;
  if (!groupId) return null;
  if (!selected.every((block) => block.groupId === groupId)) return null;
  const members = membersOfGroup(blocks, groupId);
  if (members.length < 2) return null;
  const memberIds = members.map((block) => block.id);
  const selectedSet = new Set(selectedIds);
  if (memberIds.some((id) => !selectedSet.has(id))) return null;
  if (selectedIds.some((id) => !memberIds.includes(id))) return null;
  return { groupId, memberIds, members };
}

/** Um único filho de grupo isolado (seleção via Camadas). */
export function isIsolatedGroupChildSelection(
  blocks: ComunicadoBlock[],
  selectedIds: string[],
): boolean {
  if (selectedIds.length !== 1) return false;
  const block = blocks.find((item) => item.id === selectedIds[0]);
  return Boolean(block?.groupId);
}

export function unionFramePercent(frames: ComunicadoFrame[]): ComunicadoFrame {
  if (frames.length === 0) return { x: 0, y: 0, w: 10, h: 10 };
  let x1 = Infinity;
  let y1 = Infinity;
  let x2 = -Infinity;
  let y2 = -Infinity;
  for (const frame of frames) {
    x1 = Math.min(x1, frame.x);
    y1 = Math.min(y1, frame.y);
    x2 = Math.max(x2, frame.x + frame.w);
    y2 = Math.max(y2, frame.y + frame.h);
  }
  return {
    x: x1,
    y: y1,
    w: Math.max(1, x2 - x1),
    h: Math.max(1, y2 - y1),
  };
}

export function groupBlocks(
  blocks: ComunicadoBlock[],
  selectedIds: string[],
  groupId = newComunicadoGroupId(),
): ComunicadoBlock[] {
  if (selectedIds.length < 2) return blocks;
  const idSet = new Set(selectedIds);
  return blocks.map((block) => (idSet.has(block.id) ? { ...block, groupId } : block));
}

export function ungroupBlocks(blocks: ComunicadoBlock[], selectedIds: string[]): ComunicadoBlock[] {
  if (selectedIds.length === 0) return blocks;
  const idSet = new Set(selectedIds);
  return blocks.map((block) => {
    if (!idSet.has(block.id) || !block.groupId) return block;
    const { groupId: _omit, ...rest } = block;
    return rest as ComunicadoBlock;
  });
}

export function selectedHasGroup(blocks: ComunicadoBlock[], selectedIds: string[]): boolean {
  return selectedIds.some((id) => blocks.find((block) => block.id === id)?.groupId);
}
