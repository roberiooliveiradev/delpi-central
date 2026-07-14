import type { PointerEvent as ReactPointerEvent } from "react";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import type { BlockDragMode } from "../components/useCanvasBlockInteraction";

type BeginBlockStageDragArgs = {
  event: ReactPointerEvent;
  block: ComunicadoBlock;
  isBlockSelected: (id: string) => boolean;
  selectedIds: string[];
  selectedId: string | null;
  selectBlock: (id: string, options?: { additive?: boolean }) => void;
  selectBlocksByIds: (ids: string[]) => void;
  armMultiDragSelection: (ids: string[]) => void;
  startDrag: (event: ReactPointerEvent, block: ComunicadoBlock, mode: BlockDragMode) => void;
};

/**
 * Seleção + arm de multi + startDrag move.
 * Shift = só toggle. Clique em já selecionado preserva a multi.
 * @returns false se o gesto foi só seleção (Shift).
 */
export function beginBlockStageMoveDrag(args: BeginBlockStageDragArgs): boolean {
  const {
    event,
    block,
    isBlockSelected,
    selectedIds,
    selectedId,
    selectBlock,
    selectBlocksByIds,
    armMultiDragSelection,
    startDrag,
  } = args;

  if (event.shiftKey) {
    selectBlock(block.id, { additive: true });
    return false;
  }

  let dragIds: string[];
  if (!isBlockSelected(block.id)) {
    selectBlock(block.id);
    dragIds = [block.id];
  } else {
    dragIds = [...selectedIds.filter((id) => id !== block.id), block.id];
    if (selectedId !== block.id) {
      selectBlocksByIds(dragIds);
    }
  }
  armMultiDragSelection(dragIds);
  startDrag(event, block, "move");
  return true;
}
