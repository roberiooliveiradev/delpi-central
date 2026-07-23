import {
  isComunicadoVisualBoxBlock,
  visualBoxSupportsInlineTextEditing,
  visualBoxSupportsShapeFormatting,
} from "@delpi/tv-dashboard-presentation";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import { selectedHasGroup } from "./comunicadoGrouping";
import type { LayoutAlignCommand } from "./comunicadoLayoutAlign";

export type ComunicadoContextMenuActionId =
  | "cut"
  | "copy"
  | "paste"
  | "duplicate"
  | "editText"
  | "bringToFront"
  | "sendToBack"
  | "bringForward"
  | "sendBackward"
  | "group"
  | "ungroup"
  | "regroup"
  | LayoutAlignCommand
  | "rotateCw"
  | "rotateCcw"
  | "flipH"
  | "flipV"
  | "delete"
  | "format"
  | "insertHeading"
  | "insertText"
  | "insertShape"
  | "insertDataSource";

export type ComunicadoContextMenuActionState = {
  hasSelection: boolean;
  selectionCount: number;
  canPaste: boolean;
  canEditText: boolean;
  showStyleToolbar: boolean;
  canDuplicate: boolean;
  canGroup: boolean;
  canUngroup: boolean;
  canRegroup: boolean;
  canAlignSelection: boolean;
  canDistribute: boolean;
  canRotate: boolean;
};

const SELECTION_ALIGN_COMMANDS = new Set<LayoutAlignCommand>([
  "align-left",
  "align-center-h",
  "align-right",
  "align-top",
  "align-center-v",
  "align-bottom",
]);

const DISTRIBUTE_COMMANDS = new Set<LayoutAlignCommand>(["distribute-h", "distribute-v"]);

function isLayoutAlignCommand(action: ComunicadoContextMenuActionId): action is LayoutAlignCommand {
  return (
    SELECTION_ALIGN_COMMANDS.has(action as LayoutAlignCommand) ||
    DISTRIBUTE_COMMANDS.has(action as LayoutAlignCommand) ||
    String(action).startsWith("align-slide-")
  );
}

export function resolveCanEditText(block: ComunicadoBlock | null): boolean {
  if (!block || !isComunicadoVisualBoxBlock(block)) return false;
  return visualBoxSupportsInlineTextEditing(block);
}

export function resolveShowStyleToolbar(block: ComunicadoBlock | null): boolean {
  if (!block) return false;
  if (isComunicadoVisualBoxBlock(block) && visualBoxSupportsShapeFormatting(block)) return true;
  return block.type === "heading" || block.type === "text" || block.type === "icon";
}

/**
 * Enablement do menu de contexto — espelha o ribbon (multi-seleção, grupo, align).
 * `selected` continua sendo o bloco primário (toolbar / editar texto).
 */
export function resolveContextMenuActionState(input: {
  selected: ComunicadoBlock | null;
  canPaste: boolean;
  selectedIds?: string[];
  blocks?: ComunicadoBlock[];
  lastUngroupedIds?: string[];
}): ComunicadoContextMenuActionState {
  const selectedIds =
    input.selectedIds ?? (input.selected ? [input.selected.id] : []);
  const blocks = input.blocks ?? [];
  const lastUngroupedIds = input.lastUngroupedIds ?? [];
  const selectionCount = selectedIds.length;
  const hasSelection = selectionCount > 0;
  const blockIdSet = new Set(blocks.map((block) => block.id));
  const singleSelection = selectionCount === 1;

  return {
    hasSelection,
    selectionCount,
    canPaste: input.canPaste,
    canEditText: singleSelection && resolveCanEditText(input.selected),
    showStyleToolbar: singleSelection && resolveShowStyleToolbar(input.selected),
    canDuplicate: hasSelection,
    canGroup: selectionCount >= 2,
    canUngroup: selectedHasGroup(blocks, selectedIds),
    canRegroup: lastUngroupedIds.filter((id) => blockIdSet.has(id)).length >= 2,
    canAlignSelection: selectionCount >= 2,
    canDistribute: selectionCount >= 3,
    canRotate: hasSelection,
  };
}

export function isContextMenuActionEnabled(
  action: ComunicadoContextMenuActionId,
  state: ComunicadoContextMenuActionState,
): boolean {
  if (isLayoutAlignCommand(action)) {
    if (DISTRIBUTE_COMMANDS.has(action)) return state.canDistribute;
    if (SELECTION_ALIGN_COMMANDS.has(action)) return state.canAlignSelection;
    return state.hasSelection;
  }

  switch (action) {
    case "cut":
    case "copy":
    case "delete":
    case "bringToFront":
    case "sendToBack":
    case "bringForward":
    case "sendBackward":
    case "format":
      return state.hasSelection;
    case "duplicate":
      return state.canDuplicate;
    case "group":
      return state.canGroup;
    case "ungroup":
      return state.canUngroup;
    case "regroup":
      return state.canRegroup;
    case "rotateCw":
    case "rotateCcw":
    case "flipH":
    case "flipV":
      return state.canRotate;
    case "editText":
      return state.canEditText;
    case "paste":
      // Sempre habilitado: tenta SO; interno só se o SO estiver vazio (nunca no lugar do Google).
      return true;
    case "insertHeading":
    case "insertText":
    case "insertShape":
    case "insertDataSource":
      return !state.hasSelection;
    default:
      return false;
  }
}
