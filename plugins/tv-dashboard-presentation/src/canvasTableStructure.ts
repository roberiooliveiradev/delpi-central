/**
 * Inserir faixa e auto-fit de tracks da Grade.
 */

import {
  CANVAS_TABLE_MAX_COLS,
  CANVAS_TABLE_MAX_ROWS,
  CANVAS_TABLE_MIN_TRACK_PCT,
  normalizeCanvasTableCell,
  normalizeCanvasTableCells,
  normalizeCanvasTableTrackSizes,
  type CanvasTableCell,
  type CanvasTableMerge,
  type CanvasTableOptions,
} from "./comunicadoCanvasTable";
import { normalizeCanvasTableMerges } from "./canvasTableMerge";

export type CanvasTableInsertPlacement = "before" | "after";

function clampIndex(index: number, count: number): number {
  return Math.max(0, Math.min(count, Math.round(index)));
}

function remapMergesAfterRowInsert(
  merges: readonly CanvasTableMerge[] | undefined,
  insertAt: number,
  rows: number,
  cols: number,
): CanvasTableMerge[] {
  const shifted = (merges ?? []).map((merge) => {
    if (merge.row >= insertAt) {
      return { ...merge, row: merge.row + 1 };
    }
    if (merge.row < insertAt && merge.row + merge.rowspan > insertAt) {
      return { ...merge, rowspan: merge.rowspan + 1 };
    }
    return { ...merge };
  });
  return normalizeCanvasTableMerges(shifted, rows, cols);
}

function remapMergesAfterColInsert(
  merges: readonly CanvasTableMerge[] | undefined,
  insertAt: number,
  rows: number,
  cols: number,
): CanvasTableMerge[] {
  const shifted = (merges ?? []).map((merge) => {
    if (merge.col >= insertAt) {
      return { ...merge, col: merge.col + 1 };
    }
    if (merge.col < insertAt && merge.col + merge.colspan > insertAt) {
      return { ...merge, colspan: merge.colspan + 1 };
    }
    return { ...merge };
  });
  return normalizeCanvasTableMerges(shifted, rows, cols);
}

function insertTrackSize(tracks: number[] | undefined, count: number, index: number): number[] {
  const current = normalizeCanvasTableTrackSizes(tracks, Math.max(1, count - 1));
  const next = current.slice();
  const share = 100 / count;
  next.splice(index, 0, share);
  return normalizeCanvasTableTrackSizes(next, count);
}

export function insertCanvasTableRow(params: {
  cells: CanvasTableCell[][];
  rows: number;
  cols: number;
  at: number;
  placement: CanvasTableInsertPlacement;
  merges?: readonly CanvasTableMerge[];
  rowHeights?: number[];
  canvasTableOptions?: CanvasTableOptions;
}): {
  rows: number;
  cells: CanvasTableCell[][];
  merges: CanvasTableMerge[];
  rowHeights: number[];
  canvasTableOptions?: CanvasTableOptions;
} {
  if (params.rows >= CANVAS_TABLE_MAX_ROWS) {
    return {
      rows: params.rows,
      cells: normalizeCanvasTableCells(params.cells, params.rows, params.cols),
      merges: normalizeCanvasTableMerges(params.merges, params.rows, params.cols),
      rowHeights: normalizeCanvasTableTrackSizes(params.rowHeights, params.rows),
      canvasTableOptions: params.canvasTableOptions,
    };
  }
  const insertAt = clampIndex(
    params.placement === "after" ? params.at + 1 : params.at,
    params.rows,
  );
  const nextRows = params.rows + 1;
  const blank = Array.from({ length: params.cols }, () => normalizeCanvasTableCell(""));
  const cells = normalizeCanvasTableCells(params.cells, params.rows, params.cols);
  const nextCells = cells.slice();
  nextCells.splice(insertAt, 0, blank);
  const merges = remapMergesAfterRowInsert(params.merges, insertAt, nextRows, params.cols);
  const rowHeights = insertTrackSize(params.rowHeights, nextRows, insertAt);
  return {
    rows: nextRows,
    cells: nextCells,
    merges,
    rowHeights,
    canvasTableOptions: {
      ...(params.canvasTableOptions ?? {}),
      rowHeights,
    },
  };
}

export function insertCanvasTableCol(params: {
  cells: CanvasTableCell[][];
  rows: number;
  cols: number;
  at: number;
  placement: CanvasTableInsertPlacement;
  merges?: readonly CanvasTableMerge[];
  columnWidths?: number[];
  canvasTableOptions?: CanvasTableOptions;
}): {
  cols: number;
  cells: CanvasTableCell[][];
  merges: CanvasTableMerge[];
  columnWidths: number[];
  canvasTableOptions?: CanvasTableOptions;
} {
  if (params.cols >= CANVAS_TABLE_MAX_COLS) {
    return {
      cols: params.cols,
      cells: normalizeCanvasTableCells(params.cells, params.rows, params.cols),
      merges: normalizeCanvasTableMerges(params.merges, params.rows, params.cols),
      columnWidths: normalizeCanvasTableTrackSizes(params.columnWidths, params.cols),
      canvasTableOptions: params.canvasTableOptions,
    };
  }
  const insertAt = clampIndex(
    params.placement === "after" ? params.at + 1 : params.at,
    params.cols,
  );
  const nextCols = params.cols + 1;
  const cells = normalizeCanvasTableCells(params.cells, params.rows, params.cols).map((row) => {
    const next = row.slice();
    next.splice(insertAt, 0, normalizeCanvasTableCell(""));
    return next;
  });
  const merges = remapMergesAfterColInsert(params.merges, insertAt, params.rows, nextCols);
  const columnWidths = insertTrackSize(params.columnWidths, nextCols, insertAt);
  return {
    cols: nextCols,
    cells,
    merges,
    columnWidths,
    canvasTableOptions: {
      ...(params.canvasTableOptions ?? {}),
      columnWidths,
    },
  };
}

function uniqueSortedIndices(indices: readonly number[], count: number): number[] {
  const set = new Set<number>();
  for (const raw of indices) {
    const index = Math.round(raw);
    if (index >= 0 && index < count) set.add(index);
  }
  return Array.from(set).sort((a, b) => a - b);
}

function removeTrackSizes(tracks: number[] | undefined, count: number, remove: readonly number[]): number[] {
  const current = normalizeCanvasTableTrackSizes(tracks, count);
  const next = current.filter((_, index) => !remove.includes(index));
  return normalizeCanvasTableTrackSizes(next, Math.max(1, count - remove.length));
}

function remapMergesAfterRowDelete(
  merges: readonly CanvasTableMerge[] | undefined,
  removeSorted: readonly number[],
  nextRows: number,
  cols: number,
): CanvasTableMerge[] {
  const removeSet = new Set(removeSorted);
  const remapped: CanvasTableMerge[] = [];
  for (const merge of merges ?? []) {
    if (removeSet.has(merge.row)) continue;
    let row = merge.row;
    let rowspan = merge.rowspan;
    for (const removed of removeSorted) {
      if (removed < merge.row) row -= 1;
      else if (removed > merge.row && removed < merge.row + merge.rowspan) rowspan -= 1;
    }
    if (rowspan < 1) continue;
    remapped.push({ ...merge, row, rowspan });
  }
  return normalizeCanvasTableMerges(remapped, nextRows, cols);
}

function remapMergesAfterColDelete(
  merges: readonly CanvasTableMerge[] | undefined,
  removeSorted: readonly number[],
  rows: number,
  nextCols: number,
): CanvasTableMerge[] {
  const removeSet = new Set(removeSorted);
  const remapped: CanvasTableMerge[] = [];
  for (const merge of merges ?? []) {
    if (removeSet.has(merge.col)) continue;
    let col = merge.col;
    let colspan = merge.colspan;
    for (const removed of removeSorted) {
      if (removed < merge.col) col -= 1;
      else if (removed > merge.col && removed < merge.col + merge.colspan) colspan -= 1;
    }
    if (colspan < 1) continue;
    remapped.push({ ...merge, col, colspan });
  }
  return normalizeCanvasTableMerges(remapped, rows, nextCols);
}

/** Exclui linhas (mantém mín. 1). Índices inválidos/vazios → no-op. */
export function deleteCanvasTableRows(params: {
  cells: CanvasTableCell[][];
  rows: number;
  cols: number;
  indices: readonly number[];
  merges?: readonly CanvasTableMerge[];
  rowHeights?: number[];
  canvasTableOptions?: CanvasTableOptions;
}): {
  rows: number;
  cells: CanvasTableCell[][];
  merges: CanvasTableMerge[];
  rowHeights: number[];
  canvasTableOptions?: CanvasTableOptions;
} {
  const remove = uniqueSortedIndices(params.indices, params.rows);
  if (!remove.length || remove.length >= params.rows) {
    return {
      rows: params.rows,
      cells: normalizeCanvasTableCells(params.cells, params.rows, params.cols),
      merges: normalizeCanvasTableMerges(params.merges, params.rows, params.cols),
      rowHeights: normalizeCanvasTableTrackSizes(params.rowHeights, params.rows),
      canvasTableOptions: params.canvasTableOptions,
    };
  }
  const removeSet = new Set(remove);
  const cells = normalizeCanvasTableCells(params.cells, params.rows, params.cols).filter(
    (_, row) => !removeSet.has(row),
  );
  const nextRows = cells.length;
  const rowHeights = removeTrackSizes(params.rowHeights, params.rows, remove);
  const merges = remapMergesAfterRowDelete(params.merges, remove, nextRows, params.cols);
  return {
    rows: nextRows,
    cells,
    merges,
    rowHeights,
    canvasTableOptions: {
      ...(params.canvasTableOptions ?? {}),
      rowHeights,
    },
  };
}

/** Exclui colunas (mantém mín. 1). Índices inválidos/vazios → no-op. */
export function deleteCanvasTableCols(params: {
  cells: CanvasTableCell[][];
  rows: number;
  cols: number;
  indices: readonly number[];
  merges?: readonly CanvasTableMerge[];
  columnWidths?: number[];
  canvasTableOptions?: CanvasTableOptions;
}): {
  cols: number;
  cells: CanvasTableCell[][];
  merges: CanvasTableMerge[];
  columnWidths: number[];
  canvasTableOptions?: CanvasTableOptions;
} {
  const remove = uniqueSortedIndices(params.indices, params.cols);
  if (!remove.length || remove.length >= params.cols) {
    return {
      cols: params.cols,
      cells: normalizeCanvasTableCells(params.cells, params.rows, params.cols),
      merges: normalizeCanvasTableMerges(params.merges, params.rows, params.cols),
      columnWidths: normalizeCanvasTableTrackSizes(params.columnWidths, params.cols),
      canvasTableOptions: params.canvasTableOptions,
    };
  }
  const removeSet = new Set(remove);
  const cells = normalizeCanvasTableCells(params.cells, params.rows, params.cols).map((row) =>
    row.filter((_, col) => !removeSet.has(col)),
  );
  const nextCols = cells[0]?.length ?? 1;
  const columnWidths = removeTrackSizes(params.columnWidths, params.cols, remove);
  const merges = remapMergesAfterColDelete(params.merges, remove, params.rows, nextCols);
  return {
    cols: nextCols,
    cells,
    merges,
    columnWidths,
    canvasTableOptions: {
      ...(params.canvasTableOptions ?? {}),
      columnWidths,
    },
  };
}

/**
 * Auto-fit da faixa `index` — redistribui % a partir de pesos de conteúdo (clamp mín.).
 * Não altera o frame do bloco.
 */
export function autoFitCanvasTableTrack(params: {
  tracks: number[];
  index: number;
  contentWeights: number[];
}): number[] {
  const count = Math.max(1, params.tracks.length);
  const weights = Array.from({ length: count }, (_, i) => {
    const w = Number(params.contentWeights[i]);
    return Number.isFinite(w) && w > 0 ? w : 1;
  });
  const focus = Math.max(0, Math.min(count - 1, params.index));
  const boosted = weights.map((w, i) => (i === focus ? Math.max(w, w * 1.35) : w));
  const sum = boosted.reduce((total, item) => total + item, 0) || 1;
  const next = boosted.map((w) => (w / sum) * 100);
  return normalizeCanvasTableTrackSizes(
    next.map((item) => Math.max(CANVAS_TABLE_MIN_TRACK_PCT, item)),
    count,
  );
}

/** Células de uma linha ou coluna inteira (gutter / Shift+Space / Ctrl+Space). */
export function canvasTableBandSelection(params: {
  axis: "row" | "col";
  index: number;
  rows: number;
  cols: number;
}): { row: number; col: number }[] {
  const cells: { row: number; col: number }[] = [];
  if (params.axis === "row") {
    const row = Math.max(0, Math.min(params.rows - 1, params.index));
    for (let col = 0; col < params.cols; col += 1) cells.push({ row, col });
    return cells;
  }
  const col = Math.max(0, Math.min(params.cols - 1, params.index));
  for (let row = 0; row < params.rows; row += 1) cells.push({ row, col });
  return cells;
}

/** Pesos de conteúdo por faixa (proxy de auto-fit sem DOM). */
export function canvasTableTrackContentWeights(params: {
  axis: "row" | "col";
  cells: readonly (readonly CanvasTableCell[])[];
  rows: number;
  cols: number;
}): number[] {
  const count = params.axis === "col" ? params.cols : params.rows;
  const weights = Array.from({ length: count }, () => 1);
  const matrix = normalizeCanvasTableCells(params.cells as CanvasTableCell[][], params.rows, params.cols);
  for (let row = 0; row < params.rows; row += 1) {
    for (let col = 0; col < params.cols; col += 1) {
      const cell = matrix[row]?.[col];
      const text = cell ? String(cell.text ?? cell.value ?? "").length : 0;
      const weight = Math.max(1, text);
      if (params.axis === "col") {
        weights[col] = Math.max(weights[col]!, weight);
      } else {
        weights[row] = Math.max(weights[row]!, weight);
      }
    }
  }
  return weights;
}

/**
 * Pesos por faixa a partir de geometria medida (DOM).
 * Retorna `null` se não houver rects utilizáveis — caller deve cair no proxy de conteúdo.
 */
export function canvasTableTrackRectWeights(params: {
  axis: "row" | "col";
  cellRects: readonly { row: number; col: number; width: number; height: number }[];
  rows: number;
  cols: number;
}): number[] | null {
  if (!params.cellRects.length) return null;
  const count = params.axis === "col" ? params.cols : params.rows;
  if (count < 1) return null;
  const weights = Array.from({ length: count }, () => 0);
  for (const rect of params.cellRects) {
    const size = params.axis === "col" ? Number(rect.width) : Number(rect.height);
    if (!Number.isFinite(size) || size <= 0) continue;
    if (params.axis === "col") {
      if (rect.col < 0 || rect.col >= count) continue;
      weights[rect.col] = Math.max(weights[rect.col]!, size);
    } else {
      if (rect.row < 0 || rect.row >= count) continue;
      weights[rect.row] = Math.max(weights[rect.row]!, size);
    }
  }
  if (weights.every((w) => w <= 0)) return null;
  return weights.map((w) => Math.max(1, w));
}

