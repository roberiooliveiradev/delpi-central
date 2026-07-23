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

export type ClosedGroupSelection = {
  groupId: string;
  memberIds: string[];
  members: ComunicadoBlock[];
};

/**
 * Grupos cujos membros estão **todos** na seleção (pode haver outros ids além).
 * Usado no chrome de multi-seleção de vários grupos.
 */
export function resolveFullySelectedGroups(
  blocks: ComunicadoBlock[],
  selectedIds: string[],
): ClosedGroupSelection[] {
  const selectedSet = new Set(selectedIds);
  const seen = new Set<string>();
  const out: ClosedGroupSelection[] = [];
  for (const id of selectedIds) {
    const block = blocks.find((item) => item.id === id);
    if (!block?.groupId || seen.has(block.groupId)) continue;
    seen.add(block.groupId);
    const members = membersOfGroup(blocks, block.groupId);
    if (members.length < 2) continue;
    if (!members.every((member) => selectedSet.has(member.id))) continue;
    out.push({
      groupId: block.groupId,
      memberIds: members.map((member) => member.id),
      members,
    });
  }
  return out;
}

/**
 * Seleção «pai»: todos os membros de um único groupId estão selecionados
 * (equivalente à moldura de KPI/gráfico — um chrome externo).
 */
export function resolveClosedGroupSelection(
  blocks: ComunicadoBlock[],
  selectedIds: string[],
): ClosedGroupSelection | null {
  const groups = resolveFullySelectedGroups(blocks, selectedIds);
  if (groups.length !== 1) return null;
  const only = groups[0]!;
  if (selectedIds.length !== only.memberIds.length) return null;
  return only;
}

/**
 * Subconjunto de membros de um mesmo grupo (não a seleção pai fechada).
 * Paridade com filhos de widget complexo.
 */
export function resolveGroupChildrenSelection(
  blocks: ComunicadoBlock[],
  selectedIds: string[],
): { groupId: string; memberIds: string[] } | null {
  if (selectedIds.length === 0) return null;
  if (resolveClosedGroupSelection(blocks, selectedIds)) return null;
  const selected = blocks.filter((block) => selectedIds.includes(block.id));
  if (selected.length !== selectedIds.length) return null;
  const groupId = selected[0]?.groupId;
  if (!groupId) return null;
  if (!selected.every((block) => block.groupId === groupId)) return null;
  return { groupId, memberIds: selected.map((block) => block.id) };
}

/** Um ou mais filhos de grupo isolados (Camadas / 2º clique / multi Shift). */
export function isGroupChildrenSelection(
  blocks: ComunicadoBlock[],
  selectedIds: string[],
): boolean {
  return resolveGroupChildrenSelection(blocks, selectedIds) != null;
}

/** @deprecated Preferir `isGroupChildrenSelection` (suporta multi). */
export function isIsolatedGroupChildSelection(
  blocks: ComunicadoBlock[],
  selectedIds: string[],
): boolean {
  return isGroupChildrenSelection(blocks, selectedIds);
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

/** Unidade de layout: grupo fechado (todos os membros) ou bloco solto / filho isolado. */
export type ComunicadoLayoutUnit = {
  key: string;
  memberIds: string[];
  frame: ComunicadoFrame;
};

/**
 * Particiona a seleção em unidades para align/distribute/move em lote.
 * Grupo com todos os membros selecionados → 1 unidade (bounding box).
 * Filho isolado ou bloco sem grupo → 1 unidade cada.
 */
export function partitionSelectionIntoLayoutUnits(
  blocks: ComunicadoBlock[],
  selectedIds: string[],
): ComunicadoLayoutUnit[] {
  const idSet = new Set(selectedIds);
  const selected = blocks.filter((block) => idSet.has(block.id));
  if (selected.length === 0) return [];

  const consumed = new Set<string>();
  const units: ComunicadoLayoutUnit[] = [];

  const groupIds = new Set(
    selected.map((block) => block.groupId).filter((id): id is string => Boolean(id)),
  );
  for (const groupId of groupIds) {
    const members = membersOfGroup(blocks, groupId);
    if (members.length < 2) continue;
    if (!members.every((member) => idSet.has(member.id))) continue;
    units.push({
      key: groupId,
      memberIds: members.map((member) => member.id),
      frame: unionFramePercent(members.map((member) => member.frame)),
    });
    for (const member of members) consumed.add(member.id);
  }

  for (const block of selected) {
    if (consumed.has(block.id)) continue;
    units.push({
      key: block.id,
      memberIds: [block.id],
      frame: { ...block.frame },
    });
  }

  return units;
}

/**
 * Bbox do grupo pai para contorno pontilhado enquanto filhos estão isolados.
 * null quando a seleção já é o grupo fechado ou não há filhos de grupo.
 */
export function resolveParentGroupHintFrame(
  blocks: ComunicadoBlock[],
  selectedIds: string[],
): ComunicadoFrame | null {
  if (resolveClosedGroupSelection(blocks, selectedIds)) return null;
  const children = resolveGroupChildrenSelection(blocks, selectedIds);
  if (!children) return null;
  const members = membersOfGroup(blocks, children.groupId);
  if (members.length < 2) return null;
  return unionFramePercent(members.map((member) => member.frame));
}
