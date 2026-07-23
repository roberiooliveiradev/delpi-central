import type { PointerEvent as ReactPointerEvent } from "react";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import type { BlockDragMode } from "../components/useCanvasBlockInteraction";
import { expandSelectionWithGroups } from "./comunicadoGrouping";
import {
  resolveMultiDragBlockIds,
  resolveStageSelectionHierarchy,
} from "./stageGroupedSelection";
import {
  resolveStagePointerDownAction,
  shouldArmTapDeselectOnDragCurrent,
} from "./stageInteractionPolicy";

type BeginBlockStageDragArgs = {
  event: ReactPointerEvent;
  block: ComunicadoBlock;
  blocks: ComunicadoBlock[];
  selectedIds: string[];
  selectedId: string | null;
  preferGroupChildrenSelection?: boolean;
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
 * Hierarquia: `resolveStagePointerDownAction` (policy → grupo L2/L3).
 */
export function beginBlockStageMoveDrag(args: BeginBlockStageDragArgs): boolean {
  const {
    event,
    block,
    blocks,
    selectedIds,
    selectedId,
    preferGroupChildrenSelection = false,
    selectBlock,
    selectBlocksByIds,
    armMultiDragSelection,
    startDrag,
    armTapDeselect,
  } = args;

  const action = resolveStagePointerDownAction({
    block,
    blocks,
    selectedIds,
    shiftKey: event.shiftKey,
    ctrlOrMeta: event.ctrlKey || event.metaKey,
    altKey: event.altKey,
    preferGroupChildrenSelection,
  });

  if (action.type === "subtract") {
    armTapDeselect?.(null);
    selectBlock(action.blockId, { subtract: true, expandGroup: false });
    return false;
  }

  if (action.type === "toggle-group") {
    armTapDeselect?.(null);
    /* Multi-seleção no nível do grupo fechado (não isola subitem). */
    selectBlock(action.blockId, { additive: true, expandGroup: true });
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
  const hierarchy = resolveStageSelectionHierarchy({
    blocks,
    selectedIds,
    preferGroupChildrenSelection,
  });
  const dragIds = resolveMultiDragBlockIds(blocks, selectedIds, {
    preferGroupChildrenSelection,
  });
  if (shouldArmTapDeselectOnDragCurrent(block)) {
    armTapDeselect?.(block.id);
  } else {
    armTapDeselect?.(null);
  }
  if (selectedId !== block.id && hierarchy.mode !== "children") {
    selectBlocksByIds(dragIds);
  }
  armMultiDragSelection(dragIds);
  startDrag(event, block, "move");
  return true;
}
