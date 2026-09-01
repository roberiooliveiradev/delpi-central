/**
 * Comandos de estrutura da Grade (insert na âncora) — float e ribbon.
 */

import {
  insertCanvasTableCol,
  insertCanvasTableRow,
  type CanvasTableInsertPlacement,
  type ComunicadoCanvasTableBlock,
} from "@delpi/tv-dashboard-presentation";

export type CanvasTableStructureInsertAxis = "row" | "col";

export function resolveCanvasTableInsertFocus(
  block: ComunicadoCanvasTableBlock,
  focus: { row: number; col: number } | null | undefined,
): { row: number; col: number } {
  if (focus) {
    return {
      row: Math.max(0, Math.min(block.rows - 1, focus.row)),
      col: Math.max(0, Math.min(block.cols - 1, focus.col)),
    };
  }
  return {
    row: Math.max(0, block.rows - 1),
    col: Math.max(0, block.cols - 1),
  };
}

/** Patch de bloco após inserir linha/coluna na âncora (remap merges + tracks). */
export function buildCanvasTableInsertPatch(params: {
  block: ComunicadoCanvasTableBlock;
  axis: CanvasTableStructureInsertAxis;
  placement: CanvasTableInsertPlacement;
  focus?: { row: number; col: number } | null;
}): Partial<ComunicadoCanvasTableBlock> {
  const focus = resolveCanvasTableInsertFocus(params.block, params.focus);
  const { block } = params;
  if (params.axis === "row") {
    const next = insertCanvasTableRow({
      cells: block.cells,
      rows: block.rows,
      cols: block.cols,
      at: focus.row,
      placement: params.placement,
      merges: block.merges,
      rowHeights: block.canvasTableOptions?.rowHeights,
      canvasTableOptions: block.canvasTableOptions,
    });
    return {
      rows: next.rows,
      cells: next.cells,
      merges: next.merges.length ? next.merges : undefined,
      canvasTableOptions: next.canvasTableOptions,
    };
  }
  const next = insertCanvasTableCol({
    cells: block.cells,
    rows: block.rows,
    cols: block.cols,
    at: focus.col,
    placement: params.placement,
    merges: block.merges,
    columnWidths: block.canvasTableOptions?.columnWidths,
    canvasTableOptions: block.canvasTableOptions,
  });
  return {
    cols: next.cols,
    cells: next.cells,
    merges: next.merges.length ? next.merges : undefined,
    canvasTableOptions: next.canvasTableOptions,
  };
}
