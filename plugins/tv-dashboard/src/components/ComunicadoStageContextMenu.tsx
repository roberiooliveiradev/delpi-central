import {
  isComunicadoVisualBoxBlock,
  resolveShapePrimitive,
  resolveVisualBoxChrome,
  shapeSupportsFill,
  shapeSupportsStroke,
  visualBoxSupportsShapeFormatting,
  type ComunicadoBlock,
  type ComunicadoIconBlock,
  type ComunicadoShapeKind,
} from "@delpi/tv-dashboard-presentation";
import {
  ContextMenu,
  ContextMenuDivider,
  ContextMenuItem,
  ContextMenuSub,
  ContextMenuToolbar,
  DECK_COLOR_SURFACE,
  DECK_SHAPE_DEFAULTS,
  LucideIconPickerPopover,
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
  FolderOpen,
  Image as ImageIcon,
  Monitor,
  RefreshCw,
  Replace,
  RotateCcw,
  RotateCw,
  Scissors,
  SendToBack,
  Sparkles,
  Square,
  SquarePen,
  Text,
  Trash2,
  Ungroup,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { shortcutKeysLabel } from "../content/keyboardShortcuts";
import { buildVisualBoxShapeKindPatch } from "../utils/applyVisualBoxShapeKind";
import { rememberComunicadoShape } from "../utils/comunicadoRecentShapes";
import type { LayoutAlignCommand } from "../utils/comunicadoLayoutAlign";
import {
  isContextMenuActionEnabled,
  resolveContextMenuActionState,
} from "../utils/comunicadoStageContextMenuActions";
import { resolveContextMenuIconPickerTargetId } from "../utils/contextMenuSelectionGuard";
import { ComunicadoShapeLibraryMenu } from "./ComunicadoShapeLibraryMenu";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { TvRibbonColorPicker } from "./deck/TvRibbonColorPicker";

const C = TV_DASHBOARD_HELP_TOOLTIPS.contextMenu;
const S = {
  cut: shortcutKeysLabel("cut"),
  copy: shortcutKeysLabel("copy"),
  paste: shortcutKeysLabel("paste"),
  duplicate: shortcutKeysLabel("duplicate"),
  group: shortcutKeysLabel("group"),
  ungroup: shortcutKeysLabel("ungroup"),
  delete: shortcutKeysLabel("delete"),
} as const;

type Props = {
  open: boolean;
  position: FixedPanelPoint | null;
  /**
   * Bloco sob o right-click / Shift+F10.
   * Usado no enablement mesmo antes do React commitar `selected`
   * (evita menu de «Inserir…» ao clicar num ícone ainda não selecionado).
   */
  targetBlockId?: string | null;
  onClose: () => void;
};

export function ComunicadoStageContextMenu({
  open,
  position,
  targetBlockId = null,
  onClose,
}: Props) {
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
    updateSelected,
    updateSelectedStyle,
    updateBlock,
    selectBlocksByIds,
    cancelPendingTapDeselect,
    addBlock,
    addShape,
    openDataCatalog,
    openMediaLibrary,
    triggerUpload,
    probeClipboardHasImage,
    replaceSelectedMediaFromClipboard,
  } = useComunicadoEditor();

  const pickerAnchorRef = useRef<HTMLDivElement>(null);
  const [pickerAnchorPoint, setPickerAnchorPoint] = useState<FixedPanelPoint | null>(null);
  const [shapeLibraryOpen, setShapeLibraryOpen] = useState(false);
  const [iconPickerOpen, setIconPickerOpen] = useState(false);
  /** Alvo estável do picker após fechar o menu (selection pode ter sido limpa). */
  const [pickerTargetBlockId, setPickerTargetBlockId] = useState<string | null>(null);
  const [canReplaceImageFromClipboard, setCanReplaceImageFromClipboard] = useState(false);

  const menuSelected = useMemo(() => {
    if (targetBlockId) {
      return blocks.find((block) => block.id === targetBlockId) ?? selected;
    }
    return selected;
  }, [blocks, selected, targetBlockId]);

  const menuSelectedIds = useMemo(() => {
    if (!targetBlockId) return selectedIds;
    if (selectedIds.includes(targetBlockId)) return selectedIds;
    return [targetBlockId];
  }, [selectedIds, targetBlockId]);

  /** Cancela tap-deselect armado pelo pointerdown; não força seleção no right-click. */
  useEffect(() => {
    if (!open) return;
    cancelPendingTapDeselect();
  }, [cancelPendingTapDeselect, open]);

  useEffect(() => {
    const isMedia = menuSelected?.type === "image" || menuSelected?.type === "video";
    if (!open || !isMedia) {
      setCanReplaceImageFromClipboard(false);
      return;
    }
    let cancelled = false;
    void probeClipboardHasImage().then((hasImage) => {
      if (!cancelled) setCanReplaceImageFromClipboard(hasImage);
    });
    return () => {
      cancelled = true;
    };
  }, [open, probeClipboardHasImage, menuSelected?.type]);

  const actionState = useMemo(
    () =>
      resolveContextMenuActionState({
        selected: menuSelected,
        canPaste,
        selectedIds: menuSelectedIds,
        blocks,
        lastUngroupedIds,
        canReplaceImageFromClipboard,
      }),
    [
      blocks,
      canPaste,
      canReplaceImageFromClipboard,
      lastUngroupedIds,
      menuSelected,
      menuSelectedIds,
    ],
  );

  const isShapeBlock =
    menuSelected &&
    isComunicadoVisualBoxBlock(menuSelected) &&
    visualBoxSupportsShapeFormatting(menuSelected);
  const shapePrimitive =
    isShapeBlock && menuSelected.type === "shape"
      ? resolveShapePrimitive(menuSelected.shape)
      : null;
  const shapeChrome = isShapeBlock ? resolveVisualBoxChrome(menuSelected) : null;
  const showShapeFill = shapePrimitive ? shapeSupportsFill(shapePrimitive) : false;
  const showShapeStroke = shapePrimitive ? shapeSupportsStroke(shapePrimitive) : false;

  const fillValue = isShapeBlock
    ? menuSelected.style?.fill ?? shapeChrome?.fill ?? DECK_SHAPE_DEFAULTS.fill
    : menuSelected?.style?.backgroundColor ?? DECK_COLOR_SURFACE;
  const outlineValue = isShapeBlock
    ? menuSelected.style?.stroke ??
      shapeChrome?.stroke ??
      (shapePrimitive === "line" ? DECK_SHAPE_DEFAULTS.lineStroke : DECK_SHAPE_DEFAULTS.stroke)
    : menuSelected?.style?.borderColor ?? "#cbd5e1";

  function ensureMenuSelection() {
    cancelPendingTapDeselect();
    if (menuSelectedIds.length > 0) selectBlocksByIds(menuSelectedIds);
  }

  function run(action: () => void) {
    ensureMenuSelection();
    action();
    onClose();
  }

  function runAlign(command: LayoutAlignCommand) {
    run(() => alignSelected(command));
  }

  function capturePickerAnchorAndClose() {
    if (position) setPickerAnchorPoint(position);
    onClose();
  }

  function openShapeLibraryFromMenu() {
    const targetId = menuSelected?.id ?? targetBlockId ?? null;
    setPickerTargetBlockId(targetId);
    ensureMenuSelection();
    capturePickerAnchorAndClose();
    setIconPickerOpen(false);
    setShapeLibraryOpen(true);
  }

  function openIconPickerFromMenu() {
    const targetFromMenu = targetBlockId
      ? blocks.find((block) => block.id === targetBlockId)
      : null;
    const targetId = resolveContextMenuIconPickerTargetId({
      menuSelectedId: menuSelected?.id,
      menuSelectedType: menuSelected?.type,
      targetBlockId,
      targetBlockType: targetFromMenu?.type,
      fallbackSelectedIds: menuSelectedIds,
    });
    setPickerTargetBlockId(targetId);
    ensureMenuSelection();
    capturePickerAnchorAndClose();
    setShapeLibraryOpen(false);
    setIconPickerOpen(true);
  }

  function applyShapeKind(kind: ComunicadoShapeKind) {
    const targetId = pickerTargetBlockId ?? menuSelected?.id ?? null;
    const target =
      (targetId ? blocks.find((block) => block.id === targetId) : null) ?? menuSelected;
    if (!target) return;
    const patch = buildVisualBoxShapeKindPatch(target, kind);
    if (!patch) return;
    updateBlock(target.id, patch as Partial<ComunicadoBlock>);
    selectBlocksByIds([target.id]);
    rememberComunicadoShape(kind);
    setShapeLibraryOpen(false);
    setPickerTargetBlockId(null);
  }

  function applyIconName(name: string | null) {
    const next = name?.trim() || "Star";
    const targetId = pickerTargetBlockId ?? menuSelected?.id ?? null;
    if (!targetId) return;
    const target = blocks.find((block) => block.id === targetId);
    if (!target || target.type !== "icon") return;
    updateBlock(targetId, { iconName: next } as Partial<ComunicadoIconBlock>);
    selectBlocksByIds([targetId]);
    setIconPickerOpen(false);
    setPickerTargetBlockId(null);
  }

  const pickerTargetBlock = pickerTargetBlockId
    ? blocks.find((block) => block.id === pickerTargetBlockId)
    : null;
  const selectedIconName =
    (pickerTargetBlock?.type === "icon"
      ? pickerTargetBlock.iconName
      : menuSelected?.type === "icon"
        ? menuSelected.iconName
        : null)?.trim() || "Star";

  const enabled = (action: Parameters<typeof isContextMenuActionEnabled>[0]) =>
    isContextMenuActionEnabled(action, actionState);

  return (
    <>
    <div
      ref={pickerAnchorRef}
      className="td-context-picker-anchor"
      style={{
        position: "fixed",
        left: pickerAnchorPoint?.x ?? 0,
        top: pickerAnchorPoint?.y ?? 0,
        width: 0,
        height: 0,
        pointerEvents: "none",
      }}
      aria-hidden="true"
    />
    <ComunicadoShapeLibraryMenu
      open={shapeLibraryOpen}
      anchorRef={pickerAnchorRef}
      onSelect={applyShapeKind}
      onDismiss={() => setShapeLibraryOpen(false)}
    />
    <LucideIconPickerPopover
      open={iconPickerOpen}
      onOpenChange={setIconPickerOpen}
      anchorRef={pickerAnchorRef}
      value={selectedIconName}
      nameFormat="pascal"
      curatedOnly={false}
      title="Ícones"
      showClear={false}
      portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
      ariaLabel="Biblioteca de ícones"
      onChange={applyIconName}
    />
    <ContextMenu
      open={open}
      position={position}
      onClose={onClose}
      aria-label={C.menu}
      portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
    >
      {actionState.showStyleToolbar && menuSelected ? (
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
            ) : menuSelected.type === "heading" || menuSelected.type === "text" ? (
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
            ) : menuSelected.type === "heading" ||
              menuSelected.type === "text" ||
              menuSelected.type === "icon" ? (
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
        shortcut={S.cut}
        disabled={!enabled("cut")}
        onSelect={() => run(cutSelected)}
      />
      <ContextMenuItem
        label={C.copy}
        icon={Clipboard}
        shortcut={S.copy}
        disabled={!enabled("copy")}
        onSelect={() => run(copySelected)}
      />
      <ContextMenuItem
        label={C.paste}
        icon={ClipboardPaste}
        shortcut={S.paste}
        disabled={!enabled("paste")}
        onSelect={() => run(() => void pasteFromSystemClipboard())}
      />
      {actionState.hasSelection ? (
        <ContextMenuItem
          label={C.duplicate}
          icon={Copy}
          shortcut={S.duplicate}
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
            onSelect={() => run(() => menuSelected && enterTextEdit(menuSelected.id))}
          />
        </>
      ) : null}

      {actionState.canChangeShape ? (
        <>
          <ContextMenuDivider />
          <ContextMenuItem
            label={C.changeShape}
            icon={Replace}
            disabled={!enabled("changeShape")}
            onSelect={openShapeLibraryFromMenu}
          />
        </>
      ) : null}

      {actionState.canChangeIcon ? (
        <>
          <ContextMenuDivider />
          <ContextMenuSub label={C.changeIcon} icon={RefreshCw}>
            <ContextMenuItem
              label={C.changeIconFromLibrary}
              icon={Sparkles}
              disabled={!enabled("changeIcon")}
              onSelect={openIconPickerFromMenu}
            />
          </ContextMenuSub>
        </>
      ) : null}

      {actionState.canChangeImage ? (
        <>
          <ContextMenuDivider />
          <ContextMenuSub
            label={menuSelected?.type === "video" ? C.changeVideo : C.changeImage}
            icon={ImageIcon}
          >
            <ContextMenuItem
              label={C.changeImageFromDevice}
              icon={Monitor}
              disabled={!enabled("changeImageFromDevice")}
              onSelect={() =>
                run(() => {
                  triggerUpload("block");
                })
              }
            />
            <ContextMenuItem
              label={C.changeImageFromLibrary}
              icon={FolderOpen}
              disabled={!enabled("changeImageFromLibrary")}
              onSelect={() => run(() => openMediaLibrary("block"))}
            />
            <ContextMenuItem
              label={C.changeImageFromClipboard}
              icon={ClipboardPaste}
              disabled={!enabled("changeImageFromClipboard")}
              onSelect={() => run(() => void replaceSelectedMediaFromClipboard())}
            />
          </ContextMenuSub>
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
              shortcut={S.group}
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
              shortcut={S.ungroup}
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
            shortcut={S.delete}
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
    </>
  );
}
