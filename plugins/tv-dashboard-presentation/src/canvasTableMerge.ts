/**
 * Modelo Excel-like de merges da Grade — retângulos no JSON; HTML deriva.
 */

import type { CanvasTableCellRef, CanvasTableMerge } from "./comunicadoCanvasTable";

export type { CanvasTableMerge };

export type CanvasTableMergeRect = {
  rowMin: number;
  colMin: number;
  rowMax: number;
  colMax: number;
};

export function canvasTableMergeRect(merge: CanvasTableMerge): CanvasTableMergeRect {
  return {
    rowMin: merge.row,
    colMin: merge.col,
    rowMax: merge.row + merge.rowspan - 1,
    colMax: merge.col + merge.colspan - 1,
  };
}

export function canvasTableMergeKey(merge: CanvasTableMerge): string {
  return `${merge.row}:${merge.col}:${merge.rowspan}:${merge.colspan}`;
}

function isFiniteInt(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function asInt(value: unknown): number {
  return Math.round(Number(value));
}

export function isValidCanvasTableMerge(
  merge: CanvasTableMerge,
  rows: number,
  cols: number,
): boolean {
  if (!Number.isInteger(merge.row) || !Number.isInteger(merge.col)) return false;
  if (merge.row < 0 || merge.col < 0) return false;
  if (merge.rowspan < 1 || merge.colspan < 1) return false;
  if (merge.rowspan === 1 && merge.colspan === 1) return false;
  return merge.row + merge.rowspan <= rows && merge.col + merge.colspan <= cols;
}

export function canvasTableMergesOverlap(a: CanvasTableMerge, b: CanvasTableMerge): boolean {
  const left = canvasTableMergeRect(a);
  const right = canvasTableMergeRect(b);
  return !(
    left.rowMax < right.rowMin ||
    right.rowMax < left.rowMin ||
    left.colMax < right.colMin ||
    right.colMax < left.colMin
  );
}

function mergeContains(outer: CanvasTableMerge, inner: CanvasTableMerge): boolean {
  const a = canvasTableMergeRect(outer);
  const b = canvasTableMergeRect(inner);
  return (
    b.rowMin >= a.rowMin &&
    b.rowMax <= a.rowMax &&
    b.colMin >= a.colMin &&
    b.colMax <= a.colMax
  );
}

function cellInMerge(merge: CanvasTableMerge, row: number, col: number): boolean {
  const rect = canvasTableMergeRect(merge);
  return row >= rect.rowMin && row <= rect.rowMax && col >= rect.colMin && col <= rect.colMax;
}

export function mergeAt(
  merges: readonly CanvasTableMerge[] | undefined,
  row: number,
  col: number,
): CanvasTableMerge | null {
  return merges?.find((merge) => cellInMerge(merge, row, col)) ?? null;
}

export function isCoveredCell(
  merges: readonly CanvasTableMerge[] | undefined,
  row: number,
  col: number,
): boolean {
  const found = mergeAt(merges, row, col);
  return Boolean(found && (found.row !== row || found.col !== col));
}

/** Span HTML da âncora; coberta não renderiza `td`. */
export function canvasTableCellHtmlSpan(
  merges: readonly CanvasTableMerge[] | undefined,
  row: number,
  col: number,
): { rowSpan?: number; colSpan?: number } {
  const found = mergeAt(merges, row, col);
  if (!found || found.row !== row || found.col !== col) return {};
  return {
    ...(found.rowspan > 1 ? { rowSpan: found.rowspan } : {}),
    ...(found.colspan > 1 ? { colSpan: found.colspan } : {}),
  };
}

export function parseCanvasTableMerge(raw: unknown): CanvasTableMerge | null {
  if (!raw || typeof raw !== "object") return null;
  const src = raw as Record<string, unknown>;
  if (!isFiniteInt(Number(src.row)) || !isFiniteInt(Number(src.col))) return null;
  const merge: CanvasTableMerge = {
    row: asInt(src.row),
    col: asInt(src.col),
    rowspan: asInt(src.rowspan),
    colspan: asInt(src.colspan),
  };
  return merge;
}

/** Clip / drop inválidos e rejeita overlap. */
export function normalizeCanvasTableMerges(
  raw: unknown,
  rows: number,
  cols: number,
): CanvasTableMerge[] {
  if (!Array.isArray(raw)) return [];
  const next: CanvasTableMerge[] = [];
  for (const item of raw) {
    const merge = parseCanvasTableMerge(item);
    if (!merge || !isValidCanvasTableMerge(merge, rows, cols)) continue;
    if (next.some((existing) => canvasTableMergesOverlap(existing, merge))) continue;
    next.push(merge);
  }
  return next;
}

export function expandSelectionToMerges(
  cells: readonly CanvasTableCellRef[],
  merges: readonly CanvasTableMerge[] | undefined,
): CanvasTableCellRef[] {
  if (!merges?.length || !cells.length) return [...cells];
  const byKey = new Map(cells.map((cell) => [`${cell.row}:${cell.col}`, cell] as const));
  let changed = true;
  while (changed) {
    changed = false;
    for (const cell of [...byKey.values()]) {
      const found = mergeAt(merges, cell.row, cell.col);
      if (!found) continue;
      const rect = canvasTableMergeRect(found);
      for (let row = rect.rowMin; row <= rect.rowMax; row += 1) {
        for (let col = rect.colMin; col <= rect.colMax; col += 1) {
          const key = `${row}:${col}`;
          if (byKey.has(key)) continue;
          byKey.set(key, { row, col });
          changed = true;
        }
      }
    }
  }
  return [...byKey.values()];
}

function selectionBounds(cells: readonly CanvasTableCellRef[]): {
  rowMin: number;
  colMin: number;
  rowMax: number;
  colMax: number;
} | null {
  if (!cells.length) return null;
  let rowMin = Infinity;
  let colMin = Infinity;
  let rowMax = -Infinity;
  let colMax = -Infinity;
  for (const cell of cells) {
    rowMin = Math.min(rowMin, cell.row);
    colMin = Math.min(colMin, cell.col);
    rowMax = Math.max(rowMax, cell.row);
    colMax = Math.max(colMax, cell.col);
  }
  return { rowMin, colMin, rowMax, colMax };
}

function selectionAsMerge(cells: readonly CanvasTableCellRef[]): CanvasTableMerge | null {
  const bounds = selectionBounds(cells);
  if (!bounds) return null;
  const expected = (bounds.rowMax - bounds.rowMin + 1) * (bounds.colMax - bounds.colMin + 1);
  if (cells.length !== expected) return null;
  const keys = new Set(cells.map((cell) => `${cell.row}:${cell.col}`));
  for (let row = bounds.rowMin; row <= bounds.rowMax; row += 1) {
    for (let col = bounds.colMin; col <= bounds.colMax; col += 1) {
      if (!keys.has(`${row}:${col}`)) return null;
    }
  }
  return {
    row: bounds.rowMin,
    col: bounds.colMin,
    rowspan: bounds.rowMax - bounds.rowMin + 1,
    colspan: bounds.colMax - bounds.colMin + 1,
  };
}

export function canMergeRect(
  cells: readonly CanvasTableCellRef[],
  merges: readonly CanvasTableMerge[] | undefined = [],
): boolean {
  const candidate = selectionAsMerge(cells);
  if (!candidate || (candidate.rowspan === 1 && candidate.colspan === 1)) return false;
  for (const existing of merges ?? []) {
    if (!canvasTableMergesOverlap(existing, candidate)) continue;
    if (!mergeContains(candidate, existing)) return false;
  }
  return true;
}

export function applyCanvasTableMerge(
  merges: readonly CanvasTableMerge[] | undefined,
  cells: readonly CanvasTableCellRef[],
): CanvasTableMerge[] {
  const current = merges ?? [];
  if (!canMergeRect(cells, current)) return [...current];
  const candidate = selectionAsMerge(cells);
  if (!candidate) return [...current];
  return [...current.filter((merge) => !canvasTableMergesOverlap(merge, candidate)), candidate];
}

export function unmergeCanvasTableMerges(
  merges: readonly CanvasTableMerge[] | undefined,
  cells: readonly CanvasTableCellRef[],
): CanvasTableMerge[] {
  const current = merges ?? [];
  if (!cells.length) return [...current];
  return current.filter(
    (merge) => !cells.some((cell) => cellInMerge(merge, cell.row, cell.col)),
  );
}

/** Remapeia merges ao mudar rows/cols — clip ou drop inválidos. */
export function remapCanvasTableMerges(
  merges: readonly CanvasTableMerge[] | undefined,
  rows: number,
  cols: number,
): CanvasTableMerge[] {
  return normalizeCanvasTableMerges(merges, rows, cols);
}
