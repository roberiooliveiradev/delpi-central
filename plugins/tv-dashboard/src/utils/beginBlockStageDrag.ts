import type { PointerEvent as ReactPointerEvent } from "react";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import type { BlockDragMode } from "../components/useCanvasBlockInteraction";
import { expandSelectionWithGroups, resolveClosedGroupSelection } from "./comunicadoGrouping";

type BeginBlockStageDragArgs = {
  event: ReactPointerEvent;
  block: ComunicadoBlock;
  blocks: ComunicadoBlock[];
  isBlockSelected: (id: string) => boolean;
  selectedIds: string[];
  selectedId: string | null;
  selectBlock: (id: string, options?: { additive?: boolean; subtract?: boolean; expandGroup?: boolean }) => void;
  selectBlocksByIds: (ids: string[]) => void;
  armMultiDragSelection: (ids: string[]) => void;
  startDrag: (event: ReactPointerEvent, block: ComunicadoBlock, mode: BlockDragMode) => void;
};

/**
 * Seleção + arm de multi + startDrag move.
 * - Shift = toggle multi sem expandir grupo.
 * - Alt = isola o membro (seleciona só ele) e arrasta.
 * - Ctrl/Cmd = remove o alvo da seleção (sem pan / sem isolar).
 * - 2º clique com seleção pai fechada = isola o membro clicado e arrasta só ele.
 * - Clique normal em membro = seleciona o grupo inteiro e arrasta juntos.
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

  if (event.ctrlKey || event.metaKey) {
    selectBlock(block.id, { subtract: true, expandGroup: false });
    return false;
  }

  if (event.altKey && block.groupId) {
    selectBlock(block.id, { expandGroup: false });
    armMultiDragSelection([block.id]);
    startDrag(event, block, "move");
    return true;
  }

  const closed = resolveClosedGroupSelection(blocks, selectedIds);
  if (
    closed &&
    block.groupId === closed.groupId &&
    isBlockSelected(block.id)
  ) {
    /* Seleção pai → isola o filho clicado (gesto no palco = Camadas). */
    selectBlock(block.id, { expandGroup: false });
    armMultiDragSelection([block.id]);
    startDrag(event, block, "move");
    return true;
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
