import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import { resolveClosedGroupSelection } from "./comunicadoGrouping";

/**
 * Clique duplo em membro de grupo → isola o subitem (sem expandir o grupo).
 * Retorna true se a seleção foi alterada.
 */
export function isolateGroupedBlockOnDoubleClick(params: {
  block: ComunicadoBlock;
  blocks: ComunicadoBlock[];
  selectedIds: string[];
  selectBlock: (id: string, options?: { expandGroup?: boolean }) => void;
}): boolean {
  const { block, blocks, selectedIds, selectBlock } = params;
  if (!block.groupId) return false;
  const closed = resolveClosedGroupSelection(blocks, selectedIds);
  const inClosedGroup = Boolean(closed && closed.groupId === block.groupId);
  const alreadyIsolated =
    selectedIds.length === 1 && selectedIds[0] === block.id;
  if (alreadyIsolated && !inClosedGroup) return false;
  selectBlock(block.id, { expandGroup: false });
  return true;
}
