import type { PointerEvent as ReactPointerEvent } from "react";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import type { BlockDragMode } from "../components/useCanvasBlockInteraction";
import { expandSelectionWithGroups } from "./comunicadoGrouping";
import {
  resolveGroupedBlockPointerDownAction,
  resolveStageSelectionHierarchy,
} from "./stageGroupedSelection";

type BeginBlockStageDragArgs = {
  event: ReactPointerEvent;
  block: ComunicadoBlock;
  blocks: ComunicadoBlock[];
  selectedIds: string[];
  selectedId: string | null;
  selectBlock: (
    id: string,
    options?: { additive?: boolean; subtract?: boolean; expandGroup?: boolean },
  ) => void;
  selectBlocksByIds: (ids: string[]) => void;
  armMultiDragSelection: (ids: string[]) => void;
  startDrag: (event: ReactPointerEvent, block: ComunicadoBlock, mode: BlockDragMode) => void;
  /** Marca candidato a limpar seleção se o pointerup for sem arraste. */
  armTapDeselect?: (blockId: string | null) => void;
  /** @deprecated Mantido por compatibilidade nos testes/call sites. */
  isBlockSelected?: (id: string) => boolean;
};

/**
 * Seleção + arm de multi + startDrag move.
 * Hierarquia: `resolveGroupedBlockPointerDownAction`
 * (1º clique = grupo pai, 2º = subitem, Shift = multi de filhos).
 */
export function beginBlockStageMoveDrag(args: BeginBlockStageDragArgs): boolean {
  const {
    event,
    block,
    blocks,
    selectedIds,
    selectedId,
    selectBlock,
    selectBlocksByIds,
    armMultiDragSelection,
    startDrag,
    armTapDeselect,
  } = args;

  const action = resolveGroupedBlockPointerDownAction({
    block,
    blocks,
    selectedIds,
    shiftKey: event.shiftKey,
    ctrlOrMeta: event.ctrlKey || event.metaKey,
    altKey: event.altKey,
  });

  if (action.type === "subtract") {
    armTapDeselect?.(null);
    selectBlock(action.blockId, { subtract: true, expandGroup: false });
    return false;
  }

  if (action.type === "toggle-child") {
    armTapDeselect?.(null);
    selectBlock(action.blockId, { additive: true, expandGroup: false });
    return false;
  }

  if (action.type === "isolate-child") {
    armTapDeselect?.(null);
    selectBlock(action.blockId, { expandGroup: false });
    /* Shift só entra no modo filhos; não inicia arraste. */
    if (event.shiftKey) {
      return false;
    }
    armMultiDragSelection([action.blockId]);
    startDrag(event, block, "move");
    return true;
  }

  if (action.type === "select-expand-group") {
    armTapDeselect?.(null);
    selectBlock(action.blockId);
    const dragIds = expandSelectionWithGroups(blocks, [action.blockId]);
    armMultiDragSelection(dragIds);
    startDrag(event, block, "move");
    return true;
  }

  /* drag-current-selection: filhos não reexpandem o grupo ao arrastar. */
  const hierarchy = resolveStageSelectionHierarchy({ blocks, selectedIds });
  const dragIds =
    hierarchy.mode === "children"
      ? [...selectedIds]
      : expandSelectionWithGroups(blocks, selectedIds);
  armTapDeselect?.(block.id);
  if (selectedId !== block.id && hierarchy.mode !== "children") {
    selectBlocksByIds(dragIds);
  }
  armMultiDragSelection(dragIds);
  startDrag(event, block, "move");
  return true;
}
