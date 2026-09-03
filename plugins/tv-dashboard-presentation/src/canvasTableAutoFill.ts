/**
 * AutoFill da Grade — motor puro (série numérica / texto+sufixo / cópia em tile).
 * Gesto e alça: ComunicadoCanvasTableView + overlay (E8.S31).
 */

import {
  canvasTableCellPlainText,
  normalizeCanvasTableCell,
  parseLooseNumber,
  type CanvasTableCell,
  type CanvasTableCellRef,
  type CanvasTableMerge,
} from "./comunicadoCanvasTable";
import { isCoveredCell } from "./canvasTableMerge";

export type CanvasTableBounds = {
  rowMin: number;
  colMin: number;
  rowMax: number;
  colMax: number;
};

export type CanvasTableAutoFillDirection = "up" | "down" | "left" | "right";

export type CanvasTableHostRect = {
  left: number;
  top: number;
  width: number;
  height: number;
};

export const CANVAS_TABLE_FILL_HANDLE_SIZE = 8;

const TEXT_SUFFIX_RE = /^(.*?)(\d+)$/;

export function boundsFromCanvasTableCells(
  cells: readonly CanvasTableCellRef[],
): CanvasTableBounds | null {
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

/** Quadrado ~8px no canto SE do range (coords do host). */
export function resolveCanvasTableFillHandleRect(params: {
  range: CanvasTableHostRect | null;
}): CanvasTableHostRect | null {
  const range = params.range;
  if (!range || range.width <= 0 || range.height <= 0) return null;
  const size = CANVAS_TABLE_FILL_HANDLE_SIZE;
  return {
    left: range.left + range.width - size / 2,
    top: range.top + range.height - size / 2,
    width: size,
    height: size,
  };
}

export type CanvasTableCellHostRect = {
  row: number;
  col: number;
  left: number;
  top: number;
  width: number;
  height: number;
};

/** Hit-test em coords locais do host; fallback na célula mais próxima. */
export function resolveCanvasTableCellAtHostPoint(params: {
  cellRects: readonly CanvasTableCellHostRect[];
  x: number;
  y: number;
}): CanvasTableCellRef | null {
  if (!params.cellRects.length) return null;
  for (const rect of params.cellRects) {
    if (
      params.x >= rect.left &&
      params.x < rect.left + rect.width &&
      params.y >= rect.top &&
      params.y < rect.top + rect.height
    ) {
      return { row: rect.row, col: rect.col };
    }
  }
  let best: CanvasTableCellHostRect | null = null;
  let bestDist = Infinity;
  for (const rect of params.cellRects) {
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const dist = (params.x - cx) ** 2 + (params.y - cy) ** 2;
    if (dist < bestDist) {
      bestDist = dist;
      best = rect;
    }
  }
  return best ? { row: best.row, col: best.col } : null;
}

/** União dos rects das células no bounds (preview do AutoFill). */
export function resolveCanvasTableBoundsOverlayRect(params: {
  cellRects: readonly CanvasTableCellHostRect[];
  bounds: CanvasTableBounds;
}): CanvasTableHostRect | null {
  let minL = Infinity;
  let minT = Infinity;
  let maxR = -Infinity;
  let maxB = -Infinity;
  let any = false;
  for (const rect of params.cellRects) {
    if (!inBounds(params.bounds, rect.row, rect.col)) continue;
    any = true;
    minL = Math.min(minL, rect.left);
    minT = Math.min(minT, rect.top);
    maxR = Math.max(maxR, rect.left + rect.width);
    maxB = Math.max(maxB, rect.top + rect.height);
  }
  if (!any) return null;
  return { left: minL, top: minT, width: maxR - minL, height: maxB - minT };
}

export function canvasTableCellsFromBounds(bounds: CanvasTableBounds): CanvasTableCellRef[] {
  const cells: CanvasTableCellRef[] = [];
  for (let row = bounds.rowMin; row <= bounds.rowMax; row += 1) {
    for (let col = bounds.colMin; col <= bounds.colMax; col += 1) {
      cells.push({ row, col });
    }
  }
  return cells;
}

function clampInt(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

/**
 * Estende o retângulo-fonte em um eixo dominante até a célula do ponteiro.
 * Clamp nas bordas da grade; null se o ponteiro está dentro da fonte (sem extensão).
 */
export function resolveCanvasTableAutoFillTarget(params: {
  sourceCells: readonly CanvasTableCellRef[];
  pointerCell: CanvasTableCellRef;
  rows: number;
  cols: number;
  merges?: readonly CanvasTableMerge[];
}): {
  sourceBounds: CanvasTableBounds;
  targetBounds: CanvasTableBounds;
  direction: CanvasTableAutoFillDirection;
} | null {
  void params.merges;
  const sourceBounds = boundsFromCanvasTableCells(params.sourceCells);
  if (!sourceBounds || params.rows < 1 || params.cols < 1) return null;

  const pointerRow = clampInt(Math.round(params.pointerCell.row), 0, params.rows - 1);
  const pointerCol = clampInt(Math.round(params.pointerCell.col), 0, params.cols - 1);

  if (
    pointerRow >= sourceBounds.rowMin &&
    pointerRow <= sourceBounds.rowMax &&
    pointerCol >= sourceBounds.colMin &&
    pointerCol <= sourceBounds.colMax
  ) {
    return null;
  }

  const dDown = Math.max(0, pointerRow - sourceBounds.rowMax);
  const dUp = Math.max(0, sourceBounds.rowMin - pointerRow);
  const dRight = Math.max(0, pointerCol - sourceBounds.colMax);
  const dLeft = Math.max(0, sourceBounds.colMin - pointerCol);

  const ranked: { direction: CanvasTableAutoFillDirection; dist: number }[] = [
    { direction: "down", dist: dDown },
    { direction: "up", dist: dUp },
    { direction: "right", dist: dRight },
    { direction: "left", dist: dLeft },
  ];
  ranked.sort((a, b) => b.dist - a.dist);
  const best = ranked[0];
  if (!best || best.dist <= 0) return null;

  const direction = best.direction;
  let targetBounds: CanvasTableBounds;
  switch (direction) {
    case "down":
      targetBounds = {
        rowMin: sourceBounds.rowMin,
        rowMax: clampInt(pointerRow, sourceBounds.rowMax, params.rows - 1),
        colMin: sourceBounds.colMin,
        colMax: sourceBounds.colMax,
      };
      break;
    case "up":
      targetBounds = {
        rowMin: clampInt(pointerRow, 0, sourceBounds.rowMin),
        rowMax: sourceBounds.rowMax,
        colMin: sourceBounds.colMin,
        colMax: sourceBounds.colMax,
      };
      break;
    case "right":
      targetBounds = {
        rowMin: sourceBounds.rowMin,
        rowMax: sourceBounds.rowMax,
        colMin: sourceBounds.colMin,
        colMax: clampInt(pointerCol, sourceBounds.colMax, params.cols - 1),
      };
      break;
    case "left":
      targetBounds = {
        rowMin: sourceBounds.rowMin,
        rowMax: sourceBounds.rowMax,
        colMin: clampInt(pointerCol, 0, sourceBounds.colMin),
        colMax: sourceBounds.colMax,
      };
      break;
  }

  if (
    targetBounds.rowMin === sourceBounds.rowMin &&
    targetBounds.rowMax === sourceBounds.rowMax &&
    targetBounds.colMin === sourceBounds.colMin &&
    targetBounds.colMax === sourceBounds.colMax
  ) {
    return null;
  }

  return { sourceBounds, targetBounds, direction };
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
      ? normalized.contentRuns.map((run) => ({
          ...run,
          style: run.style ? { ...run.style } : undefined,
        }))
      : undefined,
  };
}

function cellNumericValue(cell: CanvasTableCell): number | null {
  const normalized = normalizeCanvasTableCell(cell);
  if (normalized.kind === "number" && normalized.value != null && Number.isFinite(normalized.value)) {
    return normalized.value;
  }
  return parseLooseNumber(canvasTableCellPlainText(normalized));
}

function inBounds(bounds: CanvasTableBounds, row: number, col: number): boolean {
  return (
    row >= bounds.rowMin &&
    row <= bounds.rowMax &&
    col >= bounds.colMin &&
    col <= bounds.colMax
  );
}

function padDigits(n: number, width: number): string {
  const raw = String(Math.trunc(n));
  if (width <= 0 || raw.length >= width) return raw;
  return raw.padStart(width, "0");
}

type LaneMode =
  | { kind: "numeric"; values: number[]; delta: number }
  | { kind: "textSuffix"; prefix: string; values: number[]; delta: number; width: number }
  | { kind: "tile" };

function resolveLaneMode(sourceCells: CanvasTableCell[]): LaneMode {
  if (!sourceCells.length) return { kind: "tile" };

  const nums = sourceCells.map((cell) => cellNumericValue(cell));
  if (nums.every((n) => n != null)) {
    const values = nums as number[];
    const delta =
      values.length >= 2 ? values[values.length - 1]! - values[values.length - 2]! : 1;
    return { kind: "numeric", values, delta };
  }

  const parsed = sourceCells.map((cell) => {
    const text = canvasTableCellPlainText(cell);
    const match = TEXT_SUFFIX_RE.exec(text);
    if (!match) return null;
    return {
      prefix: match[1] ?? "",
      value: Number(match[2]),
      width: (match[2] ?? "").length,
    };
  });
  if (
    parsed.every((p) => p != null && Number.isFinite(p.value)) &&
    new Set(parsed.map((p) => p!.prefix)).size === 1
  ) {
    const values = parsed.map((p) => p!.value);
    const delta =
      values.length >= 2 ? values[values.length - 1]! - values[values.length - 2]! : 1;
    const width = Math.max(...parsed.map((p) => p!.width));
    return {
      kind: "textSuffix",
      prefix: parsed[0]!.prefix,
      values,
      delta,
      width,
    };
  }

  return { kind: "tile" };
}

function sourceLaneCells(
  grid: CanvasTableCell[][],
  source: CanvasTableBounds,
  direction: CanvasTableAutoFillDirection,
  laneIndex: number,
): CanvasTableCell[] {
  const cells: CanvasTableCell[] = [];
  if (direction === "down" || direction === "up") {
    for (let row = source.rowMin; row <= source.rowMax; row += 1) {
      cells.push(normalizeCanvasTableCell(grid[row]?.[laneIndex]));
    }
  } else {
    for (let col = source.colMin; col <= source.colMax; col += 1) {
      cells.push(normalizeCanvasTableCell(grid[laneIndex]?.[col]));
    }
  }
  return cells;
}

function writeSeriesCell(params: {
  prev: CanvasTableCell;
  sourceStyle: CanvasTableCell;
  nextNumber?: number;
  nextText?: string;
}): CanvasTableCell | null {
  const prev = normalizeCanvasTableCell(params.prev);
  if (prev.dataRef) return null;

  const style = params.sourceStyle.style ? { ...params.sourceStyle.style } : undefined;
  if (params.nextNumber != null && Number.isFinite(params.nextNumber)) {
    if (params.sourceStyle.kind === "number" || prev.kind === "number") {
      const next: CanvasTableCell = {
        kind: "number",
        value: params.nextNumber,
        format: params.sourceStyle.format ?? prev.format,
      };
      if (style) next.style = style;
      if (params.sourceStyle.displayFormat) {
        next.displayFormat = { ...params.sourceStyle.displayFormat };
      }
      return next;
    }
    const next: CanvasTableCell = {
      kind: "text",
      text: String(params.nextNumber),
    };
    if (style) next.style = style;
    return next;
  }

  const next: CanvasTableCell = {
    kind: "text",
    text: params.nextText ?? "",
  };
  if (style) next.style = style;
  return next;
}

/**
 * Preenche a extensão do alvo a partir da fonte (série ou tile).
 * Não altera merges; não escreve em células cobertas; série não sobrescreve dataRef.
 */
export function applyCanvasTableAutoFill(params: {
  cells: CanvasTableCell[][];
  merges?: readonly CanvasTableMerge[];
  sourceBounds: CanvasTableBounds;
  targetBounds: CanvasTableBounds;
  direction: CanvasTableAutoFillDirection;
}): CanvasTableCell[][] {
  const next = params.cells.map((row) => row.map((cell) => normalizeCanvasTableCell(cell)));
  const { sourceBounds: source, targetBounds: target, direction } = params;
  const sourceH = source.rowMax - source.rowMin + 1;
  const sourceW = source.colMax - source.colMin + 1;
  if (sourceH < 1 || sourceW < 1) return next;

  const vertical = direction === "down" || direction === "up";
  const laneStart = vertical ? source.colMin : source.rowMin;
  const laneEnd = vertical ? source.colMax : source.rowMax;

  for (let lane = laneStart; lane <= laneEnd; lane += 1) {
    const laneCells = sourceLaneCells(next, source, direction, lane);
    const mode = resolveLaneMode(laneCells);

    if (vertical) {
      for (let row = target.rowMin; row <= target.rowMax; row += 1) {
        if (inBounds(source, row, lane)) continue;
        if (isCoveredCell(params.merges, row, lane)) continue;

        if (mode.kind === "tile") {
          const srcRow =
            source.rowMin + ((((row - source.rowMin) % sourceH) + sourceH) % sourceH);
          next[row]![lane] = cloneCell(next[srcRow]![lane]!);
          continue;
        }

        const step =
          direction === "down"
            ? row - source.rowMax
            : source.rowMin - row;
        if (step <= 0) continue;
        const last = mode.values[mode.values.length - 1]!;
        const seriesValue = last + step * mode.delta;
        const sourceStyle = laneCells[laneCells.length - 1]!;
        const written =
          mode.kind === "numeric"
            ? writeSeriesCell({
                prev: next[row]![lane]!,
                sourceStyle,
                nextNumber: seriesValue,
              })
            : writeSeriesCell({
                prev: next[row]![lane]!,
                sourceStyle,
                nextText: `${mode.prefix}${padDigits(seriesValue, mode.width)}`,
              });
        if (written) next[row]![lane] = written;
      }
    } else {
      for (let col = target.colMin; col <= target.colMax; col += 1) {
        if (inBounds(source, lane, col)) continue;
        if (isCoveredCell(params.merges, lane, col)) continue;

        if (mode.kind === "tile") {
          const srcCol =
            source.colMin + ((((col - source.colMin) % sourceW) + sourceW) % sourceW);
          next[lane]![col] = cloneCell(next[lane]![srcCol]!);
          continue;
        }

        const step =
          direction === "right"
            ? col - source.colMax
            : source.colMin - col;
        if (step <= 0) continue;
        const last = mode.values[mode.values.length - 1]!;
        const seriesValue = last + step * mode.delta;
        const sourceStyle = laneCells[laneCells.length - 1]!;
        const written =
          mode.kind === "numeric"
            ? writeSeriesCell({
                prev: next[lane]![col]!,
                sourceStyle,
                nextNumber: seriesValue,
              })
            : writeSeriesCell({
                prev: next[lane]![col]!,
                sourceStyle,
                nextText: `${mode.prefix}${padDigits(seriesValue, mode.width)}`,
              });
        if (written) next[lane]![col] = written;
      }
    }
  }

  return next;
}
