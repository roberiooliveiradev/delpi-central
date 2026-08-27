/**
 * Política de clique e seleção em células da Grade (`canvas_table`).
 *
 * Paridade com texto/composito em dois estágios:
 * - 1º clique (bloco não selecionado) → seleciona o container (evento sobe ao wrap).
 * - 2º clique (bloco já selecionado) → seleciona/edita a célula.
 *
 * Multi-seleção (Excel-like):
 * - clique simples → uma célula;
 * - Ctrl/Cmd+clique → alterna célula na seleção;
 * - Shift+clique → retângulo da âncora até a célula clicada.
 */

import type { CanvasTableCellRef } from "@delpi/tv-dashboard-presentation";

export type CanvasTableCellPointerAction = "select-block" | "select-cell";

export function resolveCanvasTableCellPointerAction(params: {
  blockSelected: boolean;
}): CanvasTableCellPointerAction {
  return params.blockSelected ? "select-cell" : "select-block";
}

export type CanvasTableCellSelectionRequest = {
  cell: CanvasTableCellRef;
  additive?: boolean;
  range?: boolean;
  rowCount: number;
  colCount: number;
};

/** Seleção ativa de células na Grade. */
export type ComunicadoCanvasTableCellSelection = {
  blockId: string;
  cells: CanvasTableCellRef[];
  /** Âncora para Shift+clique (retângulo). */
  anchor: CanvasTableCellRef;
  /** Foco para binding / número / teclado. */
  focus: CanvasTableCellRef;
};

export function canvasTableCellKey(cell: CanvasTableCellRef): string {
  return `${cell.row}:${cell.col}`;
}

export function isCanvasTableCellSelected(
  selection: ComunicadoCanvasTableCellSelection | null | undefined,
  row: number,
  col: number,
): boolean {
  if (!selection) return false;
  return selection.cells.some((item) => item.row === row && item.col === col);
}

export function primaryCanvasTableCellRef(
  selection: ComunicadoCanvasTableCellSelection | null | undefined,
): CanvasTableCellRef | null {
  if (!selection?.cells.length) return null;
  return selection.focus ?? selection.cells[selection.cells.length - 1] ?? selection.cells[0] ?? null;
}

function clampCell(
  cell: CanvasTableCellRef,
  rowCount: number,
  colCount: number,
): CanvasTableCellRef {
  return {
    row: Math.max(0, Math.min(rowCount - 1, cell.row)),
    col: Math.max(0, Math.min(colCount - 1, cell.col)),
  };
}

/** Retângulo inclusivo entre duas células (ordem irrelevante). */
export function canvasTableCellRectangle(
  anchor: CanvasTableCellRef,
  target: CanvasTableCellRef,
  rowCount: number,
  colCount: number,
): CanvasTableCellRef[] {
  const a = clampCell(anchor, rowCount, colCount);
  const b = clampCell(target, rowCount, colCount);
  const rowMin = Math.min(a.row, b.row);
  const rowMax = Math.max(a.row, b.row);
  const colMin = Math.min(a.col, b.col);
  const colMax = Math.max(a.col, b.col);
  const cells: CanvasTableCellRef[] = [];
  for (let row = rowMin; row <= rowMax; row += 1) {
    for (let col = colMin; col <= colMax; col += 1) {
      cells.push({ row, col });
    }
  }
  return cells;
}

export function applyCanvasTableCellSelectionRequest(
  previous: ComunicadoCanvasTableCellSelection | null,
  blockId: string,
  request: CanvasTableCellSelectionRequest,
): ComunicadoCanvasTableCellSelection {
  const cell = clampCell(request.cell, request.rowCount, request.colCount);
  if (!request.additive && !request.range) {
    return { blockId, cells: [cell], anchor: cell, focus: cell };
  }
  if (!previous || previous.blockId !== blockId) {
    return { blockId, cells: [cell], anchor: cell, focus: cell };
  }
  if (request.range) {
    const cells = canvasTableCellRectangle(
      previous.anchor,
      cell,
      request.rowCount,
      request.colCount,
    );
    return { blockId, cells, anchor: previous.anchor, focus: cell };
  }
  const exists = previous.cells.some((item) => item.row === cell.row && item.col === cell.col);
  const nextCells = exists
    ? previous.cells.filter((item) => !(item.row === cell.row && item.col === cell.col))
    : [...previous.cells, cell];
  const cells = nextCells.length > 0 ? nextCells : [cell];
  return {
    blockId,
    cells,
    anchor: previous.anchor ?? cell,
    focus: cell,
  };
}

export function singleCanvasTableCellSelection(
  blockId: string,
  row: number,
  col: number,
): ComunicadoCanvasTableCellSelection {
  const cell = { row, col };
  return { blockId, cells: [cell], anchor: cell, focus: cell };
}

export function summarizeCanvasTableCellSelection(
  selection: ComunicadoCanvasTableCellSelection | null | undefined,
): string {
  if (!selection?.cells.length) return "Selecione células na Grade";
  if (selection.cells.length === 1) {
    const cell = selection.cells[0]!;
    return `Célula ${cell.row + 1}×${cell.col + 1}`;
  }
  return `${selection.cells.length} células`;
}
