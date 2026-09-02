/**
 * Clipboard de intervalo da Grade — texto + style + format (padrão Excel).
 */

import {
  canvasTableCellPlainText,
  normalizeCanvasTableCell,
  type CanvasTableCell,
  type CanvasTableCellRef,
  type CanvasTableMerge,
} from "./comunicadoCanvasTable";
import { expandSelectionToMerges, normalizeCanvasTableMerges } from "./canvasTableMerge";

export type CanvasTableClipboardPayload = {
  rows: number;
  cols: number;
  cells: CanvasTableCell[][];
  merges?: CanvasTableMerge[];
};

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

function cloneCell(cell: CanvasTableCell): CanvasTableCell {
  const normalized = normalizeCanvasTableCell(cell);
  return {
    ...normalized,
    style: normalized.style ? { ...normalized.style } : undefined,
    dataRef: normalized.dataRef ? { ...normalized.dataRef } : undefined,
    displayFormat: normalized.displayFormat
      ? { ...normalized.displayFormat }
      : undefined,
    series: normalized.series ? [...normalized.series] : undefined,
    contentRuns: normalized.contentRuns
      ? normalized.contentRuns.map((run) => ({ ...run, style: run.style ? { ...run.style } : undefined }))
      : undefined,
  };
}

/** Limpa conteúdo; mantém style e dataRef/dataSourceId. */
export function clearCanvasTableCellContent(cell: CanvasTableCell): CanvasTableCell {
  const prev = normalizeCanvasTableCell(cell);
  const next: CanvasTableCell = {
    kind: prev.kind === "sparkline" ? "text" : prev.kind,
    style: prev.style ? { ...prev.style } : undefined,
  };
  if (prev.dataRef) next.dataRef = { ...prev.dataRef };
  if (prev.dataSourceId) next.dataSourceId = prev.dataSourceId;
  if (prev.displayFormat) next.displayFormat = { ...prev.displayFormat };
  if (next.kind === "number") {
    next.value = null;
    next.format = prev.format;
  } else {
    next.text = "";
  }
  return next;
}

export function clearCanvasTableCellsContent(
  grid: CanvasTableCell[][],
  cells: readonly CanvasTableCellRef[],
): CanvasTableCell[][] {
  const next = grid.map((row) => row.map((cell) => normalizeCanvasTableCell(cell)));
  for (const { row, col } of cells) {
    const current = next[row]?.[col];
    if (current == null) continue;
    next[row]![col] = clearCanvasTableCellContent(current);
  }
  return next;
}

/** Remove formatos (style / contentRuns); mantém texto, value, binding e kind. */
export function clearCanvasTableCellFormats(cell: CanvasTableCell): CanvasTableCell {
  const prev = normalizeCanvasTableCell(cell);
  const next: CanvasTableCell = { kind: prev.kind };
  if (prev.text != null) next.text = prev.text;
  if (prev.value !== undefined) next.value = prev.value;
  if (prev.format) next.format = prev.format;
  if (prev.displayFormat) next.displayFormat = prev.displayFormat;
  if (prev.series) next.series = [...prev.series];
  if (prev.dataRef) next.dataRef = { ...prev.dataRef };
  if (prev.dataSourceId) next.dataSourceId = prev.dataSourceId;
  return next;
}

export function clearCanvasTableCellsFormats(
  grid: CanvasTableCell[][],
  cells: readonly CanvasTableCellRef[],
): CanvasTableCell[][] {
  const next = grid.map((row) => row.map((cell) => normalizeCanvasTableCell(cell)));
  for (const { row, col } of cells) {
    const current = next[row]?.[col];
    if (current == null) continue;
    next[row]![col] = clearCanvasTableCellFormats(current);
  }
  return next;
}

export function serializeCanvasTableClipboard(params: {
  cells: CanvasTableCell[][];
  selected: readonly CanvasTableCellRef[];
  merges?: readonly CanvasTableMerge[];
}): CanvasTableClipboardPayload | null {
  const expanded = expandSelectionToMerges(params.selected, params.merges);
  const bounds = selectionBounds(expanded);
  if (!bounds) return null;
  const rows = bounds.rowMax - bounds.rowMin + 1;
  const cols = bounds.colMax - bounds.colMin + 1;
  const cells: CanvasTableCell[][] = [];
  for (let r = 0; r < rows; r += 1) {
    const row: CanvasTableCell[] = [];
    for (let c = 0; c < cols; c += 1) {
      row.push(cloneCell(normalizeCanvasTableCell(params.cells[bounds.rowMin + r]?.[bounds.colMin + c])));
    }
    cells.push(row);
  }
  const merges = (params.merges ?? [])
    .filter((merge) => {
      const anchorIn =
        merge.row >= bounds.rowMin &&
        merge.col >= bounds.colMin &&
        merge.row + merge.rowspan - 1 <= bounds.rowMax &&
        merge.col + merge.colspan - 1 <= bounds.colMax;
      return anchorIn;
    })
    .map((merge) => ({
      row: merge.row - bounds.rowMin,
      col: merge.col - bounds.colMin,
      rowspan: merge.rowspan,
      colspan: merge.colspan,
    }));
  return {
    rows,
    cols,
    cells,
    ...(merges.length ? { merges } : {}),
  };
}

export function canvasTableClipboardToTsv(payload: CanvasTableClipboardPayload): string {
  return payload.cells
    .map((row) => row.map((cell) => canvasTableCellPlainText(cell).replace(/\t/g, " ")).join("\t"))
    .join("\n");
}

export function parseCanvasTableClipboardTsv(text: string): CanvasTableClipboardPayload | null {
  const lines = text.replace(/\r\n/g, "\n").replace(/\r/g, "\n").split("\n");
  while (lines.length && lines[lines.length - 1] === "") lines.pop();
  if (!lines.length) return null;
  const cells = lines.map((line) =>
    line.split("\t").map((part) => normalizeCanvasTableCell(part)),
  );
  const cols = Math.max(...cells.map((row) => row.length), 1);
  const normalized = cells.map((row) => {
    const next = row.slice();
    while (next.length < cols) next.push(normalizeCanvasTableCell(""));
    return next;
  });
  return { rows: normalized.length, cols, cells: normalized };
}

export function pasteCanvasTableClipboard(params: {
  cells: CanvasTableCell[][];
  payload: CanvasTableClipboardPayload;
  origin: CanvasTableCellRef;
  rows: number;
  cols: number;
  /** Merges atuais do bloco — fundidos com os remapeados do payload. */
  merges?: readonly CanvasTableMerge[];
}): { cells: CanvasTableCell[][]; merges?: CanvasTableMerge[] } {
  const next = params.cells.map((row) => row.map((cell) => normalizeCanvasTableCell(cell)));
  for (let r = 0; r < params.payload.rows; r += 1) {
    for (let c = 0; c < params.payload.cols; c += 1) {
      const row = params.origin.row + r;
      const col = params.origin.col + c;
      if (row >= params.rows || col >= params.cols) continue;
      next[row]![col] = cloneCell(params.payload.cells[r]![c]!);
    }
  }

  const payloadMerges = (params.payload.merges ?? [])
    .map((merge) => ({
      row: params.origin.row + merge.row,
      col: params.origin.col + merge.col,
      rowspan: merge.rowspan,
      colspan: merge.colspan,
    }))
    .filter(
      (merge) =>
        merge.row >= 0 &&
        merge.col >= 0 &&
        merge.row + merge.rowspan - 1 < params.rows &&
        merge.col + merge.colspan - 1 < params.cols,
    );

  if (!payloadMerges.length) {
    return { cells: next };
  }

  const pasteRect = {
    rowMin: params.origin.row,
    colMin: params.origin.col,
    rowMax: params.origin.row + params.payload.rows - 1,
    colMax: params.origin.col + params.payload.cols - 1,
  };
  const kept = (params.merges ?? []).filter((merge) => {
    const rowMax = merge.row + merge.rowspan - 1;
    const colMax = merge.col + merge.colspan - 1;
    const overlaps =
      merge.row <= pasteRect.rowMax &&
      rowMax >= pasteRect.rowMin &&
      merge.col <= pasteRect.colMax &&
      colMax >= pasteRect.colMin;
    return !overlaps;
  });
  const merges = normalizeCanvasTableMerges(
    [...kept, ...payloadMerges],
    params.rows,
    params.cols,
  );
  return { cells: next, merges };
}
