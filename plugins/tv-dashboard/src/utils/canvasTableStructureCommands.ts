/**
 * Comandos de estrutura da Grade (insert na âncora) — float e ribbon.
 */

import {
  deleteCanvasTableCols,
  deleteCanvasTableRows,
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

/** Índices únicos de linhas/colunas cobertos pela seleção (ou foco). */
export function resolveCanvasTableBandIndices(params: {
  axis: CanvasTableStructureInsertAxis;
  selection?: readonly { row: number; col: number }[];
  focus?: { row: number; col: number } | null;
}): number[] {
  const fromSelection = (params.selection ?? []).map((cell) =>
    params.axis === "row" ? cell.row : cell.col,
  );
  if (fromSelection.length) {
    return Array.from(new Set(fromSelection)).sort((a, b) => a - b);
  }
  if (params.focus) {
    return [params.axis === "row" ? params.focus.row : params.focus.col];
  }
  return [];
}

/** Patch após excluir faixas cobertas pela seleção/foco (mín. 1×1). */
export function buildCanvasTableDeletePatch(params: {
  block: ComunicadoCanvasTableBlock;
  axis: CanvasTableStructureInsertAxis;
  selection?: readonly { row: number; col: number }[];
  focus?: { row: number; col: number } | null;
}): Partial<ComunicadoCanvasTableBlock> | null {
  const { block } = params;
  const indices = resolveCanvasTableBandIndices({
    axis: params.axis,
    selection: params.selection,
    focus: params.focus ?? resolveCanvasTableInsertFocus(block, null),
  });
  if (!indices.length) return null;
  if (params.axis === "row") {
    if (indices.length >= block.rows) return null;
    const next = deleteCanvasTableRows({
      cells: block.cells,
      rows: block.rows,
      cols: block.cols,
      indices,
      merges: block.merges,
      rowHeights: block.canvasTableOptions?.rowHeights,
      canvasTableOptions: block.canvasTableOptions,
    });
    if (next.rows === block.rows) return null;
    return {
      rows: next.rows,
      cells: next.cells,
      merges: next.merges.length ? next.merges : undefined,
      canvasTableOptions: next.canvasTableOptions,
    };
  }
  if (indices.length >= block.cols) return null;
  const next = deleteCanvasTableCols({
    cells: block.cells,
    rows: block.rows,
    cols: block.cols,
    indices,
    merges: block.merges,
    columnWidths: block.canvasTableOptions?.columnWidths,
    canvasTableOptions: block.canvasTableOptions,
  });
  if (next.cols === block.cols) return null;
  return {
    cols: next.cols,
    cells: next.cells,
    merges: next.merges.length ? next.merges : undefined,
    canvasTableOptions: next.canvasTableOptions,
  };
}
