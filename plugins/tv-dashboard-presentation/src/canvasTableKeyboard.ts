/**
 * Teclado da Grade — padrão Excel: navegar vs editar.
 * Helper puro (sem DOM) para o view decidir preventDefault / onSelectCell.
 */

import type { CanvasTableCellRef } from "./comunicadoCanvasTable";

export type CanvasTableKeyboardMode = "navigate" | "edit";

export type CanvasTableKeyboardAction =
  | { type: "navigate"; next: CanvasTableCellRef; range: boolean }
  | { type: "editCaret" }
  | { type: "commitMove"; next: CanvasTableCellRef }
  | { type: "commitStay" }
  | { type: "cancelEdit" }
  | { type: "enterEdit" }
  | { type: "clearContent" }
  | { type: "insertNewline" }
  | { type: "clipboard"; op: "copy" | "cut" | "paste" }
  | { type: "ignore" };

export type ResolveCanvasTableKeyboardParams = {
  key: string;
  shift?: boolean;
  ctrl?: boolean;
  alt?: boolean;
  meta?: boolean;
  mode: CanvasTableKeyboardMode;
  row: number;
  col: number;
  rows: number;
  cols: number;
};

function clampCell(
  row: number,
  col: number,
  rows: number,
  cols: number,
): CanvasTableCellRef {
  return {
    row: Math.max(0, Math.min(rows - 1, row)),
    col: Math.max(0, Math.min(cols - 1, col)),
  };
}

function moveInRow(
  row: number,
  col: number,
  delta: number,
  rows: number,
  cols: number,
): CanvasTableCellRef {
  let nextRow = row;
  let nextCol = col + delta;
  if (nextCol < 0) {
    if (nextRow > 0) {
      nextRow -= 1;
      nextCol = cols - 1;
    } else {
      nextCol = 0;
    }
  } else if (nextCol >= cols) {
    if (nextRow < rows - 1) {
      nextRow += 1;
      nextCol = 0;
    } else {
      nextCol = cols - 1;
    }
  }
  return clampCell(nextRow, nextCol, rows, cols);
}

/** Decide a ação de teclado da Grade (navegar / editar). */
export function resolveCanvasTableKeyboardAction(
  params: ResolveCanvasTableKeyboardParams,
): CanvasTableKeyboardAction {
  const {
    key,
    shift = false,
    ctrl = false,
    alt = false,
    meta = false,
    mode,
    row,
    col,
    rows,
    cols,
  } = params;
  const mod = ctrl || meta;

  if (mode === "edit") {
    if (key === "Escape") return { type: "cancelEdit" };
    if (key === "Enter") {
      if (alt) return { type: "insertNewline" };
      if (mod) return { type: "commitStay" };
      const next = clampCell(row + (shift ? -1 : 1), col, rows, cols);
      return { type: "commitMove", next };
    }
    if (key === "Tab") {
      const next = moveInRow(row, col, shift ? -1 : 1, rows, cols);
      return { type: "commitMove", next };
    }
    if (
      key === "ArrowLeft" ||
      key === "ArrowRight" ||
      key === "ArrowUp" ||
      key === "ArrowDown" ||
      key === "Home" ||
      key === "End"
    ) {
      return { type: "editCaret" };
    }
    return { type: "ignore" };
  }

  // navigate
  if (key === "F2") return { type: "enterEdit" };
  if (key === "Escape") return { type: "ignore" };

  if (mod && (key === "c" || key === "C")) return { type: "clipboard", op: "copy" };
  if (mod && (key === "x" || key === "X")) return { type: "clipboard", op: "cut" };
  if (mod && (key === "v" || key === "V")) return { type: "clipboard", op: "paste" };

  if (key === "Delete" || key === "Backspace") return { type: "clearContent" };

  if (key === "Tab") {
    const next = moveInRow(row, col, shift ? -1 : 1, rows, cols);
    return { type: "navigate", next, range: false };
  }
  if (key === "Enter") {
    const next = clampCell(row + (shift ? -1 : 1), col, rows, cols);
    return { type: "navigate", next, range: false };
  }
  if (key === "ArrowUp") {
    return {
      type: "navigate",
      next: clampCell(row - 1, col, rows, cols),
      range: shift,
    };
  }
  if (key === "ArrowDown") {
    return {
      type: "navigate",
      next: clampCell(row + 1, col, rows, cols),
      range: shift,
    };
  }
  if (key === "ArrowLeft") {
    return {
      type: "navigate",
      next: clampCell(row, col - 1, rows, cols),
      range: shift,
    };
  }
  if (key === "ArrowRight") {
    return {
      type: "navigate",
      next: clampCell(row, col + 1, rows, cols),
      range: shift,
    };
  }

  // Digitação inicia edição (tecla imprimível, sem modificadores).
  if (
    !mod &&
    !alt &&
    key.length === 1 &&
    !key.match(/[\x00-\x1f]/)
  ) {
    return { type: "enterEdit" };
  }

  return { type: "ignore" };
}
