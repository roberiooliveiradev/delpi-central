import type { PointerEvent as ReactPointerEvent } from "react";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import type { BlockDragMode } from "../components/useCanvasBlockInteraction";
import { expandSelectionWithGroups } from "./comunicadoGrouping";

type BeginBlockStageDragArgs = {
  event: ReactPointerEvent;
  block: ComunicadoBlock;
  blocks: ComunicadoBlock[];
  isBlockSelected: (id: string) => boolean;
  selectedIds: string[];
  selectedId: string | null;
  selectBlock: (id: string, options?: { additive?: boolean; expandGroup?: boolean }) => void;
  selectBlocksByIds: (ids: string[]) => void;
  armMultiDragSelection: (ids: string[]) => void;
  startDrag: (event: ReactPointerEvent, block: ComunicadoBlock, mode: BlockDragMode) => void;
};

/**
 * Seleção + arm de multi + startDrag move.
 * Shift = só toggle. Clique em já selecionado preserva a multi.
 * Grupo: dragIds inclui todos os membros (seleção pai).
 * @returns false se o gesto foi só seleção (Shift).
 */
export function beginBlockStageMoveDrag(args: BeginBlockStageDragArgs): boolean {
  const {
    event,
    block,
    blocks,
    isBlockSelected,
    selectedIds,
    selectedId,
    selectBlock,
    selectBlocksByIds,
    armMultiDragSelection,
    startDrag,
  } = args;

  if (event.shiftKey) {
    selectBlock(block.id, { additive: true, expandGroup: false });
    return false;
  }

  let dragIds: string[];
  if (!isBlockSelected(block.id)) {
    selectBlock(block.id);
    dragIds = expandSelectionWithGroups(blocks, [block.id]);
  } else {
    dragIds = expandSelectionWithGroups(blocks, selectedIds);
    if (selectedId !== block.id) {
      selectBlocksByIds(dragIds);
    }
  }
  armMultiDragSelection(dragIds);
  startDrag(event, block, "move");
  return true;
}
