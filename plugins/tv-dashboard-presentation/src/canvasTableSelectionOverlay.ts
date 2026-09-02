/**
 * Overlay de seleção da Grade — chrome sem alterar o box das células.
 * Rects em coordenadas locais do host (não viewport / pós-scale).
 */

import { mergeAt } from "./canvasTableMerge";
import type { CanvasTableCellRef, CanvasTableMerge } from "./comunicadoCanvasTable";
import { resolveCanvasTableFillHandleRect } from "./canvasTableAutoFill";

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

/**
 * Converte rect de tela (getBoundingClientRect) para coords locais do host.
 * Obrigatório no editor: o palco aplica `transform: scale(...)` no DesignViewportStage —
 * sem dividir pela escala, overlay/handles desalinhados e handles somem no overflow.
 */
export function mapViewportRectToHostLocal(params: {
  hostRect: { left: number; top: number; width: number; height: number };
  hostOffsetWidth: number;
  hostOffsetHeight: number;
  targetRect: { left: number; top: number; width: number; height: number };
}): { left: number; top: number; width: number; height: number } {
  const scaleX =
    params.hostOffsetWidth > 0 ? params.hostRect.width / params.hostOffsetWidth : 1;
  const scaleY =
    params.hostOffsetHeight > 0 ? params.hostRect.height / params.hostOffsetHeight : 1;
  const sx = scaleX || 1;
  const sy = scaleY || 1;
  return {
    left: (params.targetRect.left - params.hostRect.left) / sx,
    top: (params.targetRect.top - params.hostRect.top) / sy,
    width: params.targetRect.width / sx,
    height: params.targetRect.height / sy,
  };
}

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

/** Alça AutoFill no canto SE do range de seleção (coords host). */
export function resolveCanvasTableSelectionFillHandleRect(params: {
  range: { left: number; top: number; width: number; height: number } | null;
}): { left: number; top: number; width: number; height: number } | null {
  return resolveCanvasTableFillHandleRect({ range: params.range });
}

export type CanvasTableTrackHandleRect = {
  axis: "col" | "row";
  index: number;
  left: number;
  top: number;
  width: number;
  height: number;
};

/** Handles nas divisórias internas — hit-area ~8px, coordenadas do host. */
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
      left: cell.left + cell.width - 4,
      top: tableTop,
      width: 8,
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
      top: cell.top + cell.height - 4,
      width: tableRight - tableLeft,
      height: 8,
    });
  }
  return handles;
}

export type CanvasTableGutterHandleRect = {
  axis: "row" | "col";
  index: number;
  left: number;
  top: number;
  width: number;
  height: number;
};

const GUTTER_HIT_PX = 14;

/** Gutter de faixa (linha à esquerda / coluna no topo) — só chrome do editor. */
export function resolveCanvasTableGutterHandles(params: {
  cellRects: readonly CanvasTableCellDomRect[];
  rows: number;
  cols: number;
}): CanvasTableGutterHandleRect[] {
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

  const gutters: CanvasTableGutterHandleRect[] = [];
  for (let row = 0; row < params.rows; row += 1) {
    const cell = byKey.get(`${row}:0`) ?? params.cellRects.find((rect) => rect.row === row);
    if (!cell) continue;
    gutters.push({
      axis: "row",
      index: row,
      left: tableLeft - GUTTER_HIT_PX,
      top: cell.top,
      width: GUTTER_HIT_PX,
      height: cell.height,
    });
  }
  for (let col = 0; col < params.cols; col += 1) {
    const cell = byKey.get(`0:${col}`) ?? params.cellRects.find((rect) => rect.col === col);
    if (!cell) continue;
    gutters.push({
      axis: "col",
      index: col,
      left: cell.left,
      top: tableTop - GUTTER_HIT_PX,
      width: cell.width,
      height: GUTTER_HIT_PX,
    });
  }
  return gutters;
}

