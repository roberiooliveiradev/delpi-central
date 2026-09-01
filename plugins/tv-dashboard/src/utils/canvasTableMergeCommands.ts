/**
 * Comandos Mesclar / Desmesclar da Grade — ribbon + atalhos Ctrl+M / Ctrl+Shift+M.
 */

import {
  applyCanvasTableMerge,
  canMergeRect,
  centerCanvasTableMergeAnchor,
  mergeAt,
  unmergeCanvasTableMerges,
  type CanvasTableCell,
  type CanvasTableCellRef,
  type CanvasTableMerge,
} from "@delpi/tv-dashboard-presentation";

export function canUnmergeCanvasTableSelection(
  merges: readonly CanvasTableMerge[] | undefined,
  cells: readonly CanvasTableCellRef[],
): boolean {
  if (!merges?.length || !cells.length) return false;
  return cells.some((cell) => Boolean(mergeAt(merges, cell.row, cell.col)));
}

export function resolveCanvasTableMergeCommand(params: {
  merges?: readonly CanvasTableMerge[];
  cells: readonly CanvasTableCellRef[];
  mode: "merge" | "unmerge";
  cellMatrix?: CanvasTableCell[][];
}): { merges: CanvasTableMerge[]; cells?: CanvasTableCell[][] } | null {
  if (params.mode === "merge") {
    if (!canMergeRect(params.cells, params.merges)) return null;
    const merges = applyCanvasTableMerge(params.merges, params.cells);
    const cells = params.cellMatrix
      ? centerCanvasTableMergeAnchor(params.cellMatrix, params.cells)
      : undefined;
    return { merges, cells };
  }
  if (!canUnmergeCanvasTableSelection(params.merges, params.cells)) return null;
  return { merges: unmergeCanvasTableMerges(params.merges, params.cells) };
}

/** Atalho: Ctrl+M mescla; Ctrl+Shift+M desmescla. */
export function resolveCanvasTableMergeShortcut(params: {
  key: string;
  ctrl: boolean;
  meta: boolean;
  shift: boolean;
}): "merge" | "unmerge" | null {
  if (!(params.ctrl || params.meta)) return null;
  if (params.key.toLowerCase() !== "m") return null;
  return params.shift ? "unmerge" : "merge";
}
