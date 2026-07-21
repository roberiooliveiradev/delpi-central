import {
  isComunicadoVisualBoxBlock,
  visualBoxSupportsInlineTextEditing,
  visualBoxSupportsShapeFormatting,
} from "@delpi/tv-dashboard-presentation";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

export type ComunicadoContextMenuActionId =
  | "cut"
  | "copy"
  | "paste"
  | "editText"
  | "bringToFront"
  | "sendToBack"
  | "bringForward"
  | "sendBackward"
  | "delete"
  | "format"
  | "insertHeading"
  | "insertText"
  | "insertShape"
  | "insertDataSource";

export type ComunicadoContextMenuActionState = {
  hasSelection: boolean;
  canPaste: boolean;
  canEditText: boolean;
  showStyleToolbar: boolean;
};

export function resolveCanEditText(block: ComunicadoBlock | null): boolean {
  if (!block || !isComunicadoVisualBoxBlock(block)) return false;
  return visualBoxSupportsInlineTextEditing(block);
}

export function resolveShowStyleToolbar(block: ComunicadoBlock | null): boolean {
  if (!block) return false;
  if (isComunicadoVisualBoxBlock(block) && visualBoxSupportsShapeFormatting(block)) return true;
  return block.type === "heading" || block.type === "text" || block.type === "icon";
}

export function resolveContextMenuActionState(input: {
  selected: ComunicadoBlock | null;
  canPaste: boolean;
}): ComunicadoContextMenuActionState {
  const hasSelection = Boolean(input.selected);
  return {
    hasSelection,
    canPaste: input.canPaste,
    canEditText: resolveCanEditText(input.selected),
    showStyleToolbar: hasSelection && resolveShowStyleToolbar(input.selected),
  };
}

export function isContextMenuActionEnabled(
  action: ComunicadoContextMenuActionId,
  state: ComunicadoContextMenuActionState,
): boolean {
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
