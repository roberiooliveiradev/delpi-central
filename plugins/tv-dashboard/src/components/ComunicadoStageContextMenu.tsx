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
  ContextMenuSub,
  ContextMenuToolbar,
  DECK_COLOR_SURFACE,
  DECK_SHAPE_DEFAULTS,
  type FixedPanelPoint,
} from "@delpi/plugin-ui/index";
import {
  AlignHorizontalJustifyCenter,
  AlignHorizontalJustifyEnd,
  AlignHorizontalJustifyStart,
  AlignVerticalJustifyCenter,
  AlignVerticalJustifyEnd,
  AlignVerticalJustifyStart,
  ArrowDown,
  ArrowUp,
  BringToFront,
  Clipboard,
  ClipboardPaste,
  Copy,
  Database,
  FlipHorizontal2,
  FlipVertical2,
  Group,
  Heading,
  Layers,
  RotateCcw,
  RotateCw,
  Scissors,
  SendToBack,
  Square,
  SquarePen,
  Text,
  Trash2,
  Ungroup,
} from "lucide-react";
import { useMemo } from "react";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { LayoutAlignCommand } from "../utils/comunicadoLayoutAlign";
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
    selectedIds,
    blocks,
    lastUngroupedIds,
    canPaste,
    cutSelected,
    copySelected,
    pasteFromSystemClipboard,
    duplicateSelected,
    enterTextEdit,
    bringToFront,
    sendToBack,
    bringForward,
    sendBackward,
    groupSelected,
    ungroupSelected,
    regroupSelected,
    alignSelected,
    rotateSelected,
    flipSelectedHorizontal,
    flipSelectedVertical,
    removeSelected,
    requestRibbonTab,
    updateSelectedStyle,
    addBlock,
    addShape,
    openDataCatalog,
  } = useComunicadoEditor();

  const actionState = useMemo(
    () =>
      resolveContextMenuActionState({
        selected,
        canPaste,
        selectedIds,
        blocks,
        lastUngroupedIds,
      }),
    [blocks, canPaste, lastUngroupedIds, selected, selectedIds],
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

  function runAlign(command: LayoutAlignCommand) {
    run(() => alignSelected(command));
  }

  const enabled = (action: Parameters<typeof isContextMenuActionEnabled>[0]) =>
    isContextMenuActionEnabled(action, actionState);

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
        disabled={!enabled("cut")}
        onSelect={() => run(cutSelected)}
      />
      <ContextMenuItem
        label={C.copy}
        icon={Clipboard}
        shortcut="Ctrl+C"
        disabled={!enabled("copy")}
        onSelect={() => run(copySelected)}
      />
      <ContextMenuItem
        label={C.paste}
        icon={ClipboardPaste}
        shortcut="Ctrl+V"
        disabled={!enabled("paste")}
        onSelect={() => run(() => void pasteFromSystemClipboard())}
      />
      {actionState.hasSelection ? (
        <ContextMenuItem
          label={C.duplicate}
          icon={Copy}
          shortcut="Ctrl+D"
          disabled={!enabled("duplicate")}
          onSelect={() => run(() => void duplicateSelected())}
        />
      ) : null}

      {!actionState.hasSelection ? (
        <>
          <ContextMenuDivider />
          <ContextMenuItem
            label={C.insertHeading}
            icon={Heading}
            disabled={!enabled("insertHeading")}
            onSelect={() => run(() => addBlock("heading"))}
          />
          <ContextMenuItem
            label={C.insertText}
            icon={Text}
            disabled={!enabled("insertText")}
            onSelect={() => run(() => addBlock("text"))}
          />
          <ContextMenuItem
            label={C.insertShape}
            icon={Square}
            disabled={!enabled("insertShape")}
            onSelect={() => run(() => addShape("rectangle"))}
          />
          <ContextMenuItem
            label={C.insertDataSource}
            icon={Database}
            disabled={!enabled("insertDataSource")}
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
            disabled={!enabled("editText")}
            onSelect={() => run(() => selected && enterTextEdit(selected.id))}
          />
        </>
      ) : null}

      {actionState.hasSelection ? (
        <>
          <ContextMenuDivider />
          <ContextMenuSub label={C.organize} icon={Layers}>
            <ContextMenuItem
              label={C.bringToFront}
              icon={BringToFront}
              disabled={!enabled("bringToFront")}
              onSelect={() => run(bringToFront)}
            />
            <ContextMenuItem
              label={C.bringForward}
              icon={ArrowUp}
              disabled={!enabled("bringForward")}
              onSelect={() => run(bringForward)}
            />
            <ContextMenuItem
              label={C.sendBackward}
              icon={ArrowDown}
              disabled={!enabled("sendBackward")}
              onSelect={() => run(sendBackward)}
            />
            <ContextMenuItem
              label={C.sendToBack}
              icon={SendToBack}
              disabled={!enabled("sendToBack")}
              onSelect={() => run(sendToBack)}
            />
          </ContextMenuSub>

          <ContextMenuSub label={C.groupMenu} icon={Group}>
            <ContextMenuItem
              label={C.group}
              icon={Group}
              disabled={!enabled("group")}
              onSelect={() => run(groupSelected)}
            />
            <ContextMenuItem
              label={C.regroup}
              icon={Group}
              disabled={!enabled("regroup")}
              onSelect={() => run(regroupSelected)}
            />
            <ContextMenuItem
              label={C.ungroup}
              icon={Ungroup}
              disabled={!enabled("ungroup")}
              onSelect={() => run(ungroupSelected)}
            />
          </ContextMenuSub>

          <ContextMenuSub label={C.align} icon={AlignHorizontalJustifyCenter}>
            <ContextMenuItem
              label={C.alignLeft}
              icon={AlignHorizontalJustifyStart}
              disabled={!enabled("align-left")}
              onSelect={() => runAlign("align-left")}
            />
            <ContextMenuItem
              label={C.alignCenterH}
              icon={AlignHorizontalJustifyCenter}
              disabled={!enabled("align-center-h")}
              onSelect={() => runAlign("align-center-h")}
            />
            <ContextMenuItem
              label={C.alignRight}
              icon={AlignHorizontalJustifyEnd}
              disabled={!enabled("align-right")}
              onSelect={() => runAlign("align-right")}
            />
            <ContextMenuDivider />
            <ContextMenuItem
              label={C.alignTop}
              icon={AlignVerticalJustifyStart}
              disabled={!enabled("align-top")}
              onSelect={() => runAlign("align-top")}
            />
            <ContextMenuItem
              label={C.alignCenterV}
              icon={AlignVerticalJustifyCenter}
              disabled={!enabled("align-center-v")}
              onSelect={() => runAlign("align-center-v")}
            />
            <ContextMenuItem
              label={C.alignBottom}
              icon={AlignVerticalJustifyEnd}
              disabled={!enabled("align-bottom")}
              onSelect={() => runAlign("align-bottom")}
            />
            <ContextMenuDivider />
            <ContextMenuItem
              label={C.distributeH}
              icon={AlignHorizontalJustifyCenter}
              disabled={!enabled("distribute-h")}
              onSelect={() => runAlign("distribute-h")}
            />
            <ContextMenuItem
              label={C.distributeV}
              icon={AlignVerticalJustifyCenter}
              disabled={!enabled("distribute-v")}
              onSelect={() => runAlign("distribute-v")}
            />
            <ContextMenuDivider />
            <ContextMenuItem
              label={C.alignSlideLeft}
              icon={AlignHorizontalJustifyStart}
              disabled={!enabled("align-slide-left")}
              onSelect={() => runAlign("align-slide-left")}
            />
            <ContextMenuItem
              label={C.alignSlideCenterH}
              icon={AlignHorizontalJustifyCenter}
              disabled={!enabled("align-slide-center-h")}
              onSelect={() => runAlign("align-slide-center-h")}
            />
            <ContextMenuItem
              label={C.alignSlideRight}
              icon={AlignHorizontalJustifyEnd}
              disabled={!enabled("align-slide-right")}
              onSelect={() => runAlign("align-slide-right")}
            />
            <ContextMenuItem
              label={C.alignSlideTop}
              icon={AlignVerticalJustifyStart}
              disabled={!enabled("align-slide-top")}
              onSelect={() => runAlign("align-slide-top")}
            />
            <ContextMenuItem
              label={C.alignSlideCenterV}
              icon={AlignVerticalJustifyCenter}
              disabled={!enabled("align-slide-center-v")}
              onSelect={() => runAlign("align-slide-center-v")}
            />
            <ContextMenuItem
              label={C.alignSlideBottom}
              icon={AlignVerticalJustifyEnd}
              disabled={!enabled("align-slide-bottom")}
              onSelect={() => runAlign("align-slide-bottom")}
            />
          </ContextMenuSub>

          <ContextMenuSub label={C.rotate} icon={RotateCw}>
            <ContextMenuItem
              label={C.rotateCw}
              icon={RotateCw}
              disabled={!enabled("rotateCw")}
              onSelect={() => run(() => rotateSelected(90))}
            />
            <ContextMenuItem
              label={C.rotateCcw}
              icon={RotateCcw}
              disabled={!enabled("rotateCcw")}
              onSelect={() => run(() => rotateSelected(-90))}
            />
            <ContextMenuDivider />
            <ContextMenuItem
              label={C.flipV}
              icon={FlipVertical2}
              disabled={!enabled("flipV")}
              onSelect={() => run(flipSelectedVertical)}
            />
            <ContextMenuItem
              label={C.flipH}
              icon={FlipHorizontal2}
              disabled={!enabled("flipH")}
              onSelect={() => run(flipSelectedHorizontal)}
            />
          </ContextMenuSub>

          <ContextMenuDivider />
          <ContextMenuItem
            label={C.delete}
            icon={Trash2}
            shortcut="Del"
            destructive
            disabled={!enabled("delete")}
            onSelect={() => run(removeSelected)}
          />
          <ContextMenuItem
            label={C.format}
            icon={Layers}
            disabled={!enabled("format")}
            onSelect={() => run(() => requestRibbonTab("shape"))}
          />
        </>
      ) : null}
    </ContextMenu>
  );
}
