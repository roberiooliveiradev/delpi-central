import {
  isComunicadoVisualBoxBlock,
  resolveShapePrimitive,
  resolveVisualBoxChrome,
  shapeSupportsFill,
  shapeSupportsStroke,
  visualBoxSupportsShapeFormatting,
} from "@delpi/tv-dashboard-presentation";
import {
  ContextMenu,
  ContextMenuDivider,
  ContextMenuItem,
  ContextMenuToolbar,
  DECK_COLOR_SURFACE,
  DECK_SHAPE_DEFAULTS,
  type FixedPanelPoint,
} from "@delpi/plugin-ui/index";
import {
  ArrowDown,
  ArrowUp,
  BringToFront,
  Clipboard,
  ClipboardPaste,
  Database,
  Heading,
  Layers,
  Scissors,
  SendToBack,
  Square,
  SquarePen,
  Text,
  Trash2,
} from "lucide-react";
import { useMemo } from "react";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  isContextMenuActionEnabled,
  resolveContextMenuActionState,
} from "../utils/comunicadoStageContextMenuActions";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { TvRibbonColorPicker } from "./deck/TvRibbonColorPicker";

const C = TV_DASHBOARD_HELP_TOOLTIPS.contextMenu;

type Props = {
  open: boolean;
  position: FixedPanelPoint | null;
  onClose: () => void;
};

export function ComunicadoStageContextMenu({ open, position, onClose }: Props) {
  const {
    selected,
    canPaste,
    cutSelected,
    copySelected,
    pasteFromSystemClipboard,
    setEditingTextId,
    bringToFront,
    sendToBack,
    bringForward,
    sendBackward,
    removeSelected,
    requestRibbonTab,
    updateSelectedStyle,
    addBlock,
    addShape,
    openDataCatalog,
  } = useComunicadoEditor();

  const actionState = useMemo(
    () => resolveContextMenuActionState({ selected, canPaste }),
    [canPaste, selected],
  );

  const isShapeBlock =
    selected && isComunicadoVisualBoxBlock(selected) && visualBoxSupportsShapeFormatting(selected);
  const shapePrimitive =
    isShapeBlock && selected.type === "shape" ? resolveShapePrimitive(selected.shape) : null;
  const shapeChrome = isShapeBlock ? resolveVisualBoxChrome(selected) : null;
  const showShapeFill = shapePrimitive ? shapeSupportsFill(shapePrimitive) : false;
  const showShapeStroke = shapePrimitive ? shapeSupportsStroke(shapePrimitive) : false;

  const fillValue = isShapeBlock
    ? selected.style?.fill ?? shapeChrome?.fill ?? DECK_SHAPE_DEFAULTS.fill
    : selected?.style?.backgroundColor ?? DECK_COLOR_SURFACE;
  const outlineValue = isShapeBlock
    ? selected.style?.stroke ??
      shapeChrome?.stroke ??
      (shapePrimitive === "line" ? DECK_SHAPE_DEFAULTS.lineStroke : DECK_SHAPE_DEFAULTS.stroke)
    : selected?.style?.borderColor ?? "#cbd5e1";

  function run(action: () => void) {
    action();
    onClose();
  }

  return (
    <ContextMenu
      open={open}
      position={position}
      onClose={onClose}
      aria-label={C.menu}
      portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
    >
      {actionState.showStyleToolbar && selected ? (
        <>
          <ContextMenuToolbar aria-label={C.quickFormat}>
            {showShapeFill ? (
              <TvRibbonColorPicker
                label={C.fill}
                ariaLabel={C.fill}
                value={fillValue}
                onChange={(color) => updateSelectedStyle({ fill: color })}
                inline
                variant="fill"
              />
            ) : selected.type === "heading" || selected.type === "text" ? (
              <TvRibbonColorPicker
                label={C.fill}
                value={fillValue}
                onChange={(color) => updateSelectedStyle({ backgroundColor: color })}
                inline
                variant="fill"
              />
            ) : null}
            {showShapeStroke ? (
              <TvRibbonColorPicker
                label={C.outline}
                value={outlineValue}
                onChange={(color) => updateSelectedStyle({ stroke: color })}
                inline
                variant="outline"
              />
            ) : selected.type === "heading" ||
              selected.type === "text" ||
              selected.type === "icon" ? (
              <TvRibbonColorPicker
                label={C.outline}
                value={outlineValue}
                onChange={(color) => updateSelectedStyle({ borderColor: color })}
                inline
                variant="outline"
              />
            ) : null}
          </ContextMenuToolbar>
          <ContextMenuDivider />
        </>
      ) : null}

      <ContextMenuItem
        label={C.cut}
        icon={Scissors}
        shortcut="Ctrl+X"
        disabled={!isContextMenuActionEnabled("cut", actionState)}
        onSelect={() => run(cutSelected)}
      />
      <ContextMenuItem
        label={C.copy}
        icon={Clipboard}
        shortcut="Ctrl+C"
        disabled={!isContextMenuActionEnabled("copy", actionState)}
        onSelect={() => run(copySelected)}
      />
      <ContextMenuItem
        label={C.paste}
        icon={ClipboardPaste}
        shortcut="Ctrl+V"
        disabled={!isContextMenuActionEnabled("paste", actionState)}
        onSelect={() => run(() => void pasteFromSystemClipboard())}
      />

      {!actionState.hasSelection ? (
        <>
          <ContextMenuDivider />
          <ContextMenuItem
            label={C.insertHeading}
            icon={Heading}
            onSelect={() => run(() => addBlock("heading"))}
          />
          <ContextMenuItem
            label={C.insertText}
            icon={Text}
            onSelect={() => run(() => addBlock("text"))}
          />
          <ContextMenuItem
            label={C.insertShape}
            icon={Square}
            onSelect={() => run(() => addShape("rectangle"))}
          />
          <ContextMenuItem
            label={C.insertDataSource}
            icon={Database}
            onSelect={() => run(() => openDataCatalog("insert"))}
          />
        </>
      ) : null}

      {actionState.canEditText ? (
        <>
          <ContextMenuDivider />
          <ContextMenuItem
            label={C.editText}
            icon={SquarePen}
            onSelect={() => run(() => selected && setEditingTextId(selected.id))}
          />
        </>
      ) : null}

      {actionState.hasSelection ? (
        <>
          <ContextMenuDivider />
          <ContextMenuItem
            label={C.bringToFront}
            icon={BringToFront}
            onSelect={() => run(bringToFront)}
          />
          <ContextMenuItem
            label={C.sendToBack}
            icon={SendToBack}
            onSelect={() => run(sendToBack)}
          />
          <ContextMenuItem
            label={C.bringForward}
            icon={ArrowUp}
            onSelect={() => run(bringForward)}
          />
          <ContextMenuItem
            label={C.sendBackward}
            icon={ArrowDown}
            onSelect={() => run(sendBackward)}
          />
        </>
      ) : null}

      {actionState.hasSelection ? (
        <>
          <ContextMenuDivider />
          <ContextMenuItem
            label={C.delete}
            icon={Trash2}
            shortcut="Del"
            destructive
            onSelect={() => run(removeSelected)}
          />
        </>
      ) : null}

      {actionState.hasSelection ? (
        <>
          <ContextMenuDivider />
          <ContextMenuItem
            label={C.format}
            icon={Layers}
            onSelect={() => run(() => requestRibbonTab("shape"))}
          />
        </>
      ) : null}
    </ContextMenu>
  );
}
