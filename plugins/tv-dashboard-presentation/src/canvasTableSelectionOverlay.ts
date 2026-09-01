/**
 * Overlay de seleção da Grade — chrome sem alterar o box das células.
 * Rects em coordenadas relativas ao host (não viewport).
 */

import { mergeAt } from "./canvasTableMerge";
import type { CanvasTableCellRef, CanvasTableMerge } from "./comunicadoCanvasTable";

export type CanvasTableCellDomRect = {
  row: number;
  col: number;
  left: number;
  top: number;
  width: number;
  height: number;
};

export type CanvasTableSelectionOverlayRects = {
  range: { left: number; top: number; width: number; height: number } | null;
  focus: { left: number; top: number; width: number; height: number } | null;
};

/** União dos retângulos das células selecionadas (range) + foco opcional. */
export function resolveCanvasTableSelectionOverlayRects(params: {
  cellRects: readonly CanvasTableCellDomRect[];
  selectedCells: readonly CanvasTableCellRef[];
  focus?: CanvasTableCellRef | null;
  merges?: readonly CanvasTableMerge[];
}): CanvasTableSelectionOverlayRects {
  const selected = params.selectedCells;
  if (!selected.length) {
    return { range: null, focus: null };
  }

  const byKey = new Map(
    params.cellRects.map((rect) => [`${rect.row}:${rect.col}`, rect] as const),
  );

  let minL = Number.POSITIVE_INFINITY;
  let minT = Number.POSITIVE_INFINITY;
  let maxR = Number.NEGATIVE_INFINITY;
  let maxB = Number.NEGATIVE_INFINITY;
  let any = false;

  for (const cell of selected) {
    const found = mergeAt(params.merges, cell.row, cell.col);
    const rect = byKey.get(
      found ? `${found.row}:${found.col}` : `${cell.row}:${cell.col}`,
    );
    if (!rect) continue;
    any = true;
    minL = Math.min(minL, rect.left);
    minT = Math.min(minT, rect.top);
    maxR = Math.max(maxR, rect.left + rect.width);
    maxB = Math.max(maxB, rect.top + rect.height);
  }

  const range = any
    ? { left: minL, top: minT, width: maxR - minL, height: maxB - minT }
    : null;

  const focusRef = params.focus ?? selected[selected.length - 1] ?? null;
  const focusMerge = focusRef ? mergeAt(params.merges, focusRef.row, focusRef.col) : null;
  const focusRect = focusRef
    ? byKey.get(
        focusMerge
          ? `${focusMerge.row}:${focusMerge.col}`
          : `${focusRef.row}:${focusRef.col}`,
      ) ?? null
    : null;
  const focus = focusRect
    ? {
        left: focusRect.left,
        top: focusRect.top,
        width: focusRect.width,
        height: focusRect.height,
      }
    : null;

  return { range, focus };
}

export type CanvasTableTrackHandleRect = {
  axis: "col" | "row";
  index: number;
  left: number;
  top: number;
  width: number;
  height: number;
};

/** Handles nas divisórias internas — hit-area ~6px, coordenadas do host. */
export function resolveCanvasTableTrackHandles(params: {
  cellRects: readonly CanvasTableCellDomRect[];
  rows: number;
  cols: number;
}): CanvasTableTrackHandleRect[] {
  const byKey = new Map(
    params.cellRects.map((rect) => [`${rect.row}:${rect.col}`, rect] as const),
  );
  let tableLeft = Number.POSITIVE_INFINITY;
  let tableTop = Number.POSITIVE_INFINITY;
  let tableRight = Number.NEGATIVE_INFINITY;
  let tableBottom = Number.NEGATIVE_INFINITY;
  for (const rect of params.cellRects) {
    tableLeft = Math.min(tableLeft, rect.left);
    tableTop = Math.min(tableTop, rect.top);
    tableRight = Math.max(tableRight, rect.left + rect.width);
    tableBottom = Math.max(tableBottom, rect.top + rect.height);
  }
  if (!Number.isFinite(tableLeft)) return [];

  const handles: CanvasTableTrackHandleRect[] = [];
  for (let col = 0; col < params.cols - 1; col += 1) {
    const cell = byKey.get(`0:${col}`) ?? params.cellRects.find((rect) => rect.col === col);
    if (!cell) continue;
    handles.push({
      axis: "col",
      index: col,
      left: cell.left + cell.width,
      top: tableTop,
      width: 6,
      height: tableBottom - tableTop,
    });
  }
  for (let row = 0; row < params.rows - 1; row += 1) {
    const cell = byKey.get(`${row}:0`) ?? params.cellRects.find((rect) => rect.row === row);
    if (!cell) continue;
    handles.push({
      axis: "row",
      index: row,
      left: tableLeft,
      top: cell.top + cell.height,
      width: tableRight - tableLeft,
      height: 6,
    });
  }
  return handles;
}
