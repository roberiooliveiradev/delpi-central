import { newBlockId, type ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

export function newComunicadoGroupId(): string {
  return `grp_${newBlockId()}`;
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
  return [...expanded];
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
