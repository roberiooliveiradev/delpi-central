/**
 * Comandos canônicos da seleção da Grade — ribbon, float e menu só disparam.
 * Funções puras: devolvem patch de células / bloco; o caller chama updateBlock.
 */

import {
  clearCanvasTableCellsContent,
  clearCanvasTableCellsFormats,
  normalizeCanvasTableCell,
  type CanvasTableCell,
  type CanvasTableCellRef,
  type ComunicadoCanvasTableBlock,
} from "@delpi/tv-dashboard-presentation";

import {
  resolveCanvasTableMergeCommand,
} from "./canvasTableMergeCommands";
import {
  buildCanvasTableInsertPatch,
  type CanvasTableStructureInsertAxis,
} from "./canvasTableStructureCommands";
import type { CanvasTableInsertPlacement } from "@delpi/tv-dashboard-presentation";

export type CanvasTableCellStylePatch = NonNullable<CanvasTableCell["style"]>;

/** Aplica patch de estilo em cada célula da seleção. */
export function patchCanvasTableCellsStyle(params: {
  cells: CanvasTableCell[][];
  selection: readonly CanvasTableCellRef[];
  stylePatch: CanvasTableCellStylePatch;
}): CanvasTableCell[][] {
  const next = params.cells.map((row) => row.map((cell) => normalizeCanvasTableCell(cell)));
  for (const { row, col } of params.selection) {
    const current = next[row]?.[col];
    if (current == null) continue;
    next[row]![col] = {
      ...current,
      style: { ...(current.style ?? {}), ...params.stylePatch },
    };
  }
  return next;
}

/** Mesclar / desmesclar — wrapper tipado do merge command (incl. merge-and-center). */
export function applyCanvasTableMergeToBlock(params: {
  block: ComunicadoCanvasTableBlock;
  selection: readonly CanvasTableCellRef[];
  mode: "merge" | "unmerge";
}): Partial<ComunicadoCanvasTableBlock> | null {
  if (!params.selection.length) return null;
  const next = resolveCanvasTableMergeCommand({
    merges: params.block.merges,
    cells: params.selection,
    mode: params.mode,
    cellMatrix: params.mode === "merge" ? params.block.cells : undefined,
  });
  if (!next) return null;
  return {
    merges: next.merges.length ? next.merges : undefined,
    ...(next.cells ? { cells: next.cells } : {}),
  };
}

/** Inserir linha/coluna na âncora — reusa structure commands. */
export function insertCanvasTableBand(params: {
  block: ComunicadoCanvasTableBlock;
  axis: CanvasTableStructureInsertAxis;
  placement: CanvasTableInsertPlacement;
  focus?: { row: number; col: number } | null;
}): Partial<ComunicadoCanvasTableBlock> {
  return buildCanvasTableInsertPatch(params);
}

export function clearCanvasTableSelectionContent(params: {
  cells: CanvasTableCell[][];
  selection: readonly CanvasTableCellRef[];
}): CanvasTableCell[][] {
  return clearCanvasTableCellsContent(params.cells, params.selection);
}

export function clearCanvasTableSelectionFormats(params: {
  cells: CanvasTableCell[][];
  selection: readonly CanvasTableCellRef[];
}): CanvasTableCell[][] {
  return clearCanvasTableCellsFormats(params.cells, params.selection);
}
