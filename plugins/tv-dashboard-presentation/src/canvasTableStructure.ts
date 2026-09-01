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

