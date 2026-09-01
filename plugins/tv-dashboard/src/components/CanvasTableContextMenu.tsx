import {
  ContextMenu,
  ContextMenuDivider,
  ContextMenuItem,
  type FixedPanelPoint,
} from "@delpi/plugin-ui/index";
import {
  AlignCenter,
  Combine,
  Eraser,
  RemoveFormatting,
  TableCellsSplit,
  WrapText,
} from "lucide-react";
import {
  canMergeRect,
  clearCanvasTableCellsContent,
  clearCanvasTableCellsFormats,
  normalizeCanvasTableCell,
  type CanvasTableCell,
  type ComunicadoCanvasTableBlock,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import {
  canUnmergeCanvasTableSelection,
  resolveCanvasTableMergeCommand,
} from "../utils/canvasTableMergeCommands";
import { buildCanvasTableInsertPatch } from "../utils/canvasTableStructureCommands";

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

  function clearContent() {
    if (!hasSelection) return;
    updateBlock(block.id, {
      cells: clearCanvasTableCellsContent(block.cells, cells),
    });
  }

  function clearFormats() {
    if (!hasSelection) return;
    updateBlock(block.id, {
      cells: clearCanvasTableCellsFormats(block.cells, cells),
    });
  }

  function merge() {
    const next = resolveCanvasTableMergeCommand({
      merges: block.merges,
      cells,
      mode: "merge",
      cellMatrix: block.cells,
    });
    if (!next) return;
    updateBlock(block.id, {
      merges: next.merges.length ? next.merges : undefined,
      ...(next.cells ? { cells: next.cells } : {}),
    });
  }

  function unmerge() {
    const next = resolveCanvasTableMergeCommand({
      merges: block.merges,
      cells,
      mode: "unmerge",
    });
    if (!next) return;
    updateBlock(block.id, {
      merges: next.merges.length ? next.merges : undefined,
    });
  }

  function insertRow(placement: "before" | "after") {
    updateBlock(
      block.id,
      buildCanvasTableInsertPatch({
        block,
        axis: "row",
        placement,
        focus,
      }),
    );
  }

  function insertCol(placement: "before" | "after") {
    updateBlock(
      block.id,
      buildCanvasTableInsertPatch({
        block,
        axis: "col",
        placement,
        focus,
      }),
    );
  }

  function patchStyle(stylePatch: NonNullable<CanvasTableCell["style"]>) {
    if (!hasSelection) return;
    const nextCells = block.cells.map((row) => row.map((cell) => normalizeCanvasTableCell(cell)));
    for (const { row, col } of cells) {
      const current = nextCells[row]?.[col];
      if (current == null) continue;
      nextCells[row]![col] = {
        ...normalizeCanvasTableCell(current),
        style: { ...(current.style ?? {}), ...stylePatch },
      };
    }
    updateBlock(block.id, { cells: nextCells });
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
        label="Mesclar"
        icon={Combine}
        disabled={!canMerge}
        onSelect={() => run(merge)}
      />
      <ContextMenuItem
        label="Desmesclar"
        icon={TableCellsSplit}
        disabled={!canUnmerge}
        onSelect={() => run(unmerge)}
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
      <ContextMenuItem
        label="Quebrar texto"
        icon={WrapText}
        disabled={!hasSelection}
        onSelect={() => run(() => patchStyle({ whiteSpace: "pre-wrap" }))}
      />
      <ContextMenuItem
        label="Não quebrar"
        disabled={!hasSelection}
        onSelect={() => run(() => patchStyle({ whiteSpace: "nowrap" }))}
      />
      <ContextMenuItem
        label="Alinhar ao topo"
        disabled={!hasSelection}
        onSelect={() => run(() => patchStyle({ verticalAlign: "top" }))}
      />
      <ContextMenuItem
        label="Alinhar ao meio"
        disabled={!hasSelection}
        onSelect={() => run(() => patchStyle({ verticalAlign: "middle" }))}
      />
      <ContextMenuItem
        label="Alinhar à base"
        disabled={!hasSelection}
        onSelect={() => run(() => patchStyle({ verticalAlign: "bottom" }))}
      />
      <ContextMenuItem
        label="Centralizar"
        icon={AlignCenter}
        disabled={!hasSelection}
        onSelect={() => run(() => patchStyle({ textAlign: "center" }))}
      />
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
