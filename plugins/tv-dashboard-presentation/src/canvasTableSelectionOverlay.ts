/**
 * Overlay de seleção da Grade — chrome sem alterar o box das células.
 * Rects em coordenadas relativas ao host (não viewport).
 */

import type { CanvasTableCellRef } from "./comunicadoCanvasTable";

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
    const rect = byKey.get(`${cell.row}:${cell.col}`);
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
  const focusRect = focusRef
    ? byKey.get(`${focusRef.row}:${focusRef.col}`) ?? null
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
