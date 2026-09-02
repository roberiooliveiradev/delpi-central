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

import {
  expandSelectionToMerges,
  mergeAt,
  canvasTableBandSelection,
  type CanvasTableCellRef,
  type CanvasTableMerge,
} from "@delpi/tv-dashboard-presentation";

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
  /** Seleciona linha/coluna inteira (gutter / Shift+Space / Ctrl+Space). */
  band?: "row" | "col";
  /** Ctrl+A — todas as células da Grade. */
  selectAll?: boolean;
  rowCount: number;
  colCount: number;
  merges?: readonly CanvasTableMerge[];
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

function focusForMerge(
  cell: CanvasTableCellRef,
  merges: readonly CanvasTableMerge[] | undefined,
): CanvasTableCellRef {
  const found = mergeAt(merges, cell.row, cell.col);
  return found ? { row: found.row, col: found.col } : cell;
}

export function applyCanvasTableCellSelectionRequest(
  previous: ComunicadoCanvasTableCellSelection | null,
  blockId: string,
  request: CanvasTableCellSelectionRequest,
): ComunicadoCanvasTableCellSelection {
  const cell = clampCell(request.cell, request.rowCount, request.colCount);
  const focus = focusForMerge(cell, request.merges);

  if (request.selectAll) {
    const all = canvasTableCellRectangle(
      { row: 0, col: 0 },
      { row: request.rowCount - 1, col: request.colCount - 1 },
      request.rowCount,
      request.colCount,
    );
    const cells = expandSelectionToMerges(all, request.merges);
    return {
      blockId,
      cells,
      anchor: { row: 0, col: 0 },
      focus: cells[0] ?? { row: 0, col: 0 },
    };
  }

  if (request.band) {
    const bandCells = canvasTableBandSelection({
      axis: request.band,
      index: request.band === "row" ? cell.row : cell.col,
      rows: request.rowCount,
      cols: request.colCount,
    });
    const cells = expandSelectionToMerges(bandCells, request.merges);
    return {
      blockId,
      cells,
      anchor: cells[0] ?? focus,
      focus,
    };
  }

  if (!request.additive && !request.range) {
    return {
      blockId,
      cells: expandSelectionToMerges([cell], request.merges),
      anchor: focus,
      focus,
    };
  }
  if (!previous || previous.blockId !== blockId) {
    return {
      blockId,
      cells: expandSelectionToMerges([cell], request.merges),
      anchor: focus,
      focus,
    };
  }
  if (request.range) {
    const cells = expandSelectionToMerges(
      canvasTableCellRectangle(
        previous.anchor,
        cell,
        request.rowCount,
        request.colCount,
      ),
      request.merges,
    );
    return { blockId, cells, anchor: previous.anchor, focus };
  }
  const unit = expandSelectionToMerges([cell], request.merges);
  const unitKeys = new Set(unit.map((item) => canvasTableCellKey(item)));
  const unitSelected = unit.every((item) =>
    previous.cells.some((current) => current.row === item.row && current.col === item.col),
  );
  const nextCells = unitSelected
    ? previous.cells.filter((item) => !unitKeys.has(canvasTableCellKey(item)))
    : [
        ...previous.cells,
        ...unit.filter(
          (item) =>
            !previous.cells.some((current) => current.row === item.row && current.col === item.col),
        ),
      ];
  const cells = nextCells.length > 0 ? nextCells : unit;
  return {
    blockId,
    cells,
    anchor: previous.anchor ?? focus,
    focus,
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
