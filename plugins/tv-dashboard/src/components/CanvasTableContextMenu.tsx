import {
  ContextMenu,
  ContextMenuDivider,
  ContextMenuItem,
  type FixedPanelPoint,
} from "@delpi/plugin-ui/index";
import {
  ClipboardCopy,
  ClipboardPaste,
  Combine,
  Eraser,
  RemoveFormatting,
  Scissors,
  TableCellsSplit,
} from "lucide-react";
import {
  canMergeRect,
  canvasTableClipboardToTsv,
  clearCanvasTableCellsContent,
  getCanvasTableSessionClipboard,
  nextCanvasTableWhiteSpaceToggle,
  normalizeCanvasTableCell,
  parseCanvasTableClipboardTsv,
  pasteCanvasTableClipboard,
  serializeCanvasTableClipboard,
  setCanvasTableSessionClipboard,
  type ComunicadoCanvasTableBlock,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import { CanvasTableCellFormatMenu } from "./CanvasTableCellFormatMenu";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { canUnmergeCanvasTableSelection } from "../utils/canvasTableMergeCommands";
import {
  applyCanvasTableMergeToBlock,
  clearCanvasTableSelectionContent,
  clearCanvasTableSelectionFormats,
  insertCanvasTableBand,
  patchCanvasTableCellsStyle,
  type CanvasTableCellStylePatch,
} from "../utils/canvasTableSelectionCommands";

type Props = {
  block: ComunicadoCanvasTableBlock;
  open: boolean;
  position: FixedPanelPoint | null;
  onClose: () => void;
};

/**
 * Menu contextual da Grade — ContextMenu do kit (AnchoredPanelPortal interno).
 */
export function CanvasTableContextMenu({ block, open, position, onClose }: Props) {
  const { updateBlock, selectedCanvasTableCell } = useComunicadoEditor();
  const cellSelection =
    selectedCanvasTableCell?.blockId === block.id ? selectedCanvasTableCell : null;
  const cells = cellSelection?.cells ?? [];
  const focus = cellSelection?.focus ?? cells[0] ?? null;

  const canMerge = Boolean(cells.length && canMergeRect(cells, block.merges));
  const canUnmerge = Boolean(
    cells.length && canUnmergeCanvasTableSelection(block.merges, cells),
  );
  const hasSelection = cells.length > 0;
  const focusCell = focus
    ? normalizeCanvasTableCell(block.cells[focus.row]?.[focus.col])
    : null;

  function clearContent() {
    if (!hasSelection) return;
    updateBlock(block.id, {
      cells: clearCanvasTableSelectionContent({ cells: block.cells, selection: cells }),
    });
  }

  function clearFormats() {
    if (!hasSelection) return;
    updateBlock(block.id, {
      cells: clearCanvasTableSelectionFormats({ cells: block.cells, selection: cells }),
    });
  }

  function merge(mode: "merge" | "unmerge") {
    const patch = applyCanvasTableMergeToBlock({ block, selection: cells, mode });
    if (!patch) return;
    updateBlock(block.id, patch);
  }

  function insertRow(placement: "before" | "after") {
    updateBlock(
      block.id,
      insertCanvasTableBand({ block, axis: "row", placement, focus }),
    );
  }

  function insertCol(placement: "before" | "after") {
    updateBlock(
      block.id,
      insertCanvasTableBand({ block, axis: "col", placement, focus }),
    );
  }

  function patchStyle(stylePatch: CanvasTableCellStylePatch) {
    if (!hasSelection) return;
    updateBlock(block.id, {
      cells: patchCanvasTableCellsStyle({
        cells: block.cells,
        selection: cells,
        stylePatch,
      }),
    });
  }

  function copySelection(cut: boolean) {
    if (!hasSelection) return;
    const payload = serializeCanvasTableClipboard({
      cells: block.cells,
      selected: cells,
      merges: block.merges,
    });
    if (!payload) return;
    setCanvasTableSessionClipboard(payload);
    void navigator.clipboard?.writeText?.(canvasTableClipboardToTsv(payload));
    if (cut) {
      updateBlock(block.id, {
        cells: clearCanvasTableCellsContent(block.cells, cells),
      });
    }
  }

  function pasteSelection() {
    const origin = focus ?? cells[0];
    if (!origin) return;
    const applyPayload = (payload: NonNullable<ReturnType<typeof getCanvasTableSessionClipboard>>) => {
      const pasted = pasteCanvasTableClipboard({
        cells: block.cells,
        payload,
        origin,
        rows: block.rows,
        cols: block.cols,
        merges: block.merges,
      });
      updateBlock(block.id, {
        cells: pasted.cells,
        ...(pasted.merges
          ? { merges: pasted.merges.length ? pasted.merges : undefined }
          : {}),
      });
    };
    const session = getCanvasTableSessionClipboard();
    if (session) {
      applyPayload(session);
      return;
    }
    void navigator.clipboard?.readText?.().then((text) => {
      const payload = parseCanvasTableClipboardTsv(text);
      if (payload) applyPayload(payload);
    });
  }

  function run(fn: () => void) {
    fn();
    onClose();
  }

  return (
    <ContextMenu
      open={open}
      position={position}
      onClose={onClose}
      aria-label="Menu da Grade"
      portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
    >
      <ContextMenuItem
        label="Copiar"
        icon={ClipboardCopy}
        disabled={!hasSelection}
        onSelect={() => run(() => copySelection(false))}
      />
      <ContextMenuItem
        label="Recortar"
        icon={Scissors}
        disabled={!hasSelection}
        onSelect={() => run(() => copySelection(true))}
      />
      <ContextMenuItem
        label="Colar"
        icon={ClipboardPaste}
        disabled={!focus}
        onSelect={() => run(pasteSelection)}
      />
      <ContextMenuDivider />
      <ContextMenuItem
        label="Mesclar"
        icon={Combine}
        disabled={!canMerge}
        onSelect={() => run(() => merge("merge"))}
      />
      <ContextMenuItem
        label="Desmesclar"
        icon={TableCellsSplit}
        disabled={!canUnmerge}
        onSelect={() => run(() => merge("unmerge"))}
      />
      <ContextMenuDivider />
      <ContextMenuItem
        label="Inserir linha acima"
        disabled={!focus}
        onSelect={() => run(() => insertRow("before"))}
      />
      <ContextMenuItem
        label="Inserir linha abaixo"
        disabled={!focus}
        onSelect={() => run(() => insertRow("after"))}
      />
      <ContextMenuItem
        label="Inserir coluna à esquerda"
        disabled={!focus}
        onSelect={() => run(() => insertCol("before"))}
      />
      <ContextMenuItem
        label="Inserir coluna à direita"
        disabled={!focus}
        onSelect={() => run(() => insertCol("after"))}
      />
      <ContextMenuDivider />
      {hasSelection && focusCell ? (
        <CanvasTableCellFormatMenu
          textAlign={focusCell.style?.textAlign}
          verticalAlign={focusCell.style?.verticalAlign}
          whiteSpace={focusCell.style?.whiteSpace}
          color={focusCell.style?.color}
          backgroundColor={focusCell.style?.backgroundColor}
          onAlign={(align) => run(() => patchStyle({ textAlign: align }))}
          onVerticalAlign={(align) => run(() => patchStyle({ verticalAlign: align }))}
          onToggleWrap={() =>
            run(() =>
              patchStyle({
                whiteSpace: nextCanvasTableWhiteSpaceToggle(focusCell.style?.whiteSpace),
              }),
            )
          }
          onSetNowrap={() => run(() => patchStyle({ whiteSpace: "nowrap" }))}
          onColorChange={(color) => run(() => patchStyle({ color }))}
          onBackgroundChange={(color) => run(() => patchStyle({ backgroundColor: color }))}
          onNoFill={() => run(() => patchStyle({ backgroundColor: undefined }))}
        />
      ) : null}
      <ContextMenuDivider />
      <ContextMenuItem
        label="Limpar conteúdo"
        icon={Eraser}
        disabled={!hasSelection}
        onSelect={() => run(clearContent)}
      />
      <ContextMenuItem
        label="Limpar formatos"
        icon={RemoveFormatting}
        disabled={!hasSelection}
        onSelect={() => run(clearFormats)}
      />
    </ContextMenu>
  );
}
