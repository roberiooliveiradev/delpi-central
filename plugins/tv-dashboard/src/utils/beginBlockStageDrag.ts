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
  selectBlock: (id: string, options?: { additive?: boolean; subtract?: boolean; expandGroup?: boolean }) => void;
  selectBlocksByIds: (ids: string[]) => void;
  armMultiDragSelection: (ids: string[]) => void;
  startDrag: (event: ReactPointerEvent, block: ComunicadoBlock, mode: BlockDragMode) => void;
  /** Marca candidato a limpar seleção se o pointerup for sem arraste. */
  armTapDeselect?: (blockId: string | null) => void;
};

/**
 * Seleção + arm de multi + startDrag move.
 * - Shift = toggle multi sem expandir grupo.
 * - Alt = isola o membro (seleciona só ele) e arrasta.
 * - Ctrl/Cmd = remove o alvo da seleção (sem pan / sem isolar).
 * - Toque em item já selecionado sem arrastar = limpa seleção (`armTapDeselect`).
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
    armTapDeselect,
  } = args;

  if (event.shiftKey) {
    armTapDeselect?.(null);
    selectBlock(block.id, { additive: true, expandGroup: false });
    return false;
  }

  if (event.ctrlKey || event.metaKey) {
    armTapDeselect?.(null);
    selectBlock(block.id, { subtract: true, expandGroup: false });
    return false;
  }

  if (event.altKey && block.groupId) {
    armTapDeselect?.(null);
    selectBlock(block.id, { expandGroup: false });
    armMultiDragSelection([block.id]);
    startDrag(event, block, "move");
    return true;
  }

  const alreadySelected = isBlockSelected(block.id);
  armTapDeselect?.(alreadySelected ? block.id : null);

  let dragIds: string[];
  if (!alreadySelected) {
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
